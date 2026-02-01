"""
SQLite storage for Discord messages.

No AI/embeddings - simple text storage with FTS5 for search.
Cost: $0 (no API calls)
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from contextlib import contextmanager

from src.utils import get_logger

logger = get_logger(__name__)

# Default database path
DEFAULT_DB_PATH = Path("data/messages.db")


@dataclass
class StoredMessage:
    """Stored message data."""
    message_id: str
    channel_id: str
    channel_name: str
    guild_id: Optional[str]
    author_id: str
    author_name: str
    author_display_name: str
    content: str
    timestamp: str
    url: str
    category_id: Optional[str] = None
    author_roles: Optional[List[str]] = None
    attachments_count: int = 0


@dataclass
class SearchResult:
    """Search result with relevance score."""
    message: StoredMessage
    score: float
    snippet: str  # Highlighted snippet from FTS


class SQLiteMessageStorage:
    """
    SQLite-based message storage with FTS5 full-text search.
    
    Benefits over vector embeddings:
    - Zero AI costs (no embedding API calls)
    - Faster indexing
    - Exact keyword matching
    - SQL flexibility for analytics
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize SQLite storage.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
        
        # Silent init
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with context manager."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _init_database(self):
        """Initialize database schema with FTS5."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Main messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT UNIQUE NOT NULL,
                    channel_id TEXT NOT NULL,
                    channel_name TEXT NOT NULL,
                    guild_id TEXT,
                    category_id TEXT,
                    author_id TEXT NOT NULL,
                    author_name TEXT NOT NULL,
                    author_display_name TEXT,
                    author_roles TEXT,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    url TEXT,
                    attachments_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # FTS5 virtual table for full-text search
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
                    message_id,
                    content,
                    author_name,
                    channel_name,
                    content='messages',
                    content_rowid='id',
                    tokenize='porter unicode61'
                )
            """)
            
            # Triggers to keep FTS in sync
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
                    INSERT INTO messages_fts(rowid, message_id, content, author_name, channel_name)
                    VALUES (new.id, new.message_id, new.content, new.author_name, new.channel_name);
                END
            """)
            
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
                    INSERT INTO messages_fts(messages_fts, rowid, message_id, content, author_name, channel_name)
                    VALUES ('delete', old.id, old.message_id, old.content, old.author_name, old.channel_name);
                END
            """)
            
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS messages_au AFTER UPDATE ON messages BEGIN
                    INSERT INTO messages_fts(messages_fts, rowid, message_id, content, author_name, channel_name)
                    VALUES ('delete', old.id, old.message_id, old.content, old.author_name, old.channel_name);
                    INSERT INTO messages_fts(rowid, message_id, content, author_name, channel_name)
                    VALUES (new.id, new.message_id, new.content, new.author_name, new.channel_name);
                END
            """)
            
            # Indexes for fast lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_channel 
                ON messages(channel_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_author 
                ON messages(author_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_timestamp 
                ON messages(timestamp)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_category 
                ON messages(category_id)
            """)
            
            pass  # Schema ready
    
    def store_message(self, message: StoredMessage) -> bool:
        """
        Store a message in the database.
        
        Args:
            message: Message to store
            
        Returns:
            True if stored, False if duplicate
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR IGNORE INTO messages (
                        message_id, channel_id, channel_name, guild_id, category_id,
                        author_id, author_name, author_display_name, author_roles,
                        content, timestamp, url, attachments_count
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    message.message_id,
                    message.channel_id,
                    message.channel_name,
                    message.guild_id,
                    message.category_id,
                    message.author_id,
                    message.author_name,
                    message.author_display_name,
                    json.dumps(message.author_roles) if message.author_roles else None,
                    message.content,
                    message.timestamp,
                    message.url,
                    message.attachments_count,
                ))
                
                if cursor.rowcount > 0:
                    logger.debug(
                        "message_stored",
                        message_id=message.message_id,
                        channel=message.channel_name,
                    )
                    return True
                return False
                
        except Exception as e:
            logger.error(
                "message_storage_failed",
                message_id=message.message_id,
                error=str(e),
            )
            return False
    
    def store_messages_batch(self, messages: List[StoredMessage]) -> int:
        """
        Store multiple messages in a single transaction.
        
        Args:
            messages: List of messages to store
            
        Returns:
            Number of messages stored
        """
        if not messages:
            return 0
        
        stored_count = 0
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                for message in messages:
                    cursor.execute("""
                        INSERT OR IGNORE INTO messages (
                            message_id, channel_id, channel_name, guild_id, category_id,
                            author_id, author_name, author_display_name, author_roles,
                            content, timestamp, url, attachments_count
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        message.message_id,
                        message.channel_id,
                        message.channel_name,
                        message.guild_id,
                        message.category_id,
                        message.author_id,
                        message.author_name,
                        message.author_display_name,
                        json.dumps(message.author_roles) if message.author_roles else None,
                        message.content,
                        message.timestamp,
                        message.url,
                        message.attachments_count,
                    ))
                    
                    if cursor.rowcount > 0:
                        stored_count += 1
                
                # Log if some messages were skipped (duplicates)
                skipped = len(messages) - stored_count
                if skipped > 0:
                    logger.debug(
                        "batch_messages_stored",
                        total=len(messages),
                        stored=stored_count,
                        skipped_duplicates=skipped,
                    )
                
        except Exception as e:
            logger.error(
                "batch_storage_failed",
                total=len(messages),
                error=str(e),
            )
        
        return stored_count
    
    def message_exists(self, message_id: str) -> bool:
        """
        Check if message already exists.
        
        Args:
            message_id: Discord message ID
            
        Returns:
            True if exists
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM messages WHERE message_id = ? LIMIT 1",
                (message_id,)
            )
            return cursor.fetchone() is not None
    
    def search(
        self,
        query: str,
        channel_id: Optional[str] = None,
        author_id: Optional[str] = None,
        category_ids_exclude: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[SearchResult]:
        """
        Full-text search for messages.
        
        Uses FTS5 with BM25 ranking.
        
        Args:
            query: Search query
            channel_id: Filter by channel (optional)
            author_id: Filter by author (optional)
            category_ids_exclude: Categories to exclude
            limit: Max results
            
        Returns:
            List of search results with scores
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Build query with filters
                sql = """
                    SELECT 
                        m.*,
                        bm25(messages_fts) as score,
                        snippet(messages_fts, 1, '<b>', '</b>', '...', 32) as snippet
                    FROM messages_fts
                    JOIN messages m ON messages_fts.rowid = m.id
                    WHERE messages_fts MATCH ?
                """
                params = [query]
                
                if channel_id:
                    sql += " AND m.channel_id = ?"
                    params.append(channel_id)
                
                if author_id:
                    sql += " AND m.author_id = ?"
                    params.append(author_id)
                
                if category_ids_exclude:
                    placeholders = ",".join("?" * len(category_ids_exclude))
                    sql += f" AND (m.category_id IS NULL OR m.category_id NOT IN ({placeholders}))"
                    params.extend(category_ids_exclude)
                
                sql += " ORDER BY score LIMIT ?"
                params.append(limit)
                
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                
                results = []
                for row in rows:
                    message = StoredMessage(
                        message_id=row["message_id"],
                        channel_id=row["channel_id"],
                        channel_name=row["channel_name"],
                        guild_id=row["guild_id"],
                        category_id=row["category_id"],
                        author_id=row["author_id"],
                        author_name=row["author_name"],
                        author_display_name=row["author_display_name"],
                        author_roles=json.loads(row["author_roles"]) if row["author_roles"] else None,
                        content=row["content"],
                        timestamp=row["timestamp"],
                        url=row["url"],
                        attachments_count=row["attachments_count"],
                    )
                    
                    results.append(SearchResult(
                        message=message,
                        score=abs(row["score"]),  # BM25 returns negative scores
                        snippet=row["snippet"],
                    ))
                
                logger.debug(
                    "fts_search_completed",
                    query=query[:50],
                    results=len(results),
                    channel_filter=channel_id is not None,
                )
                
                return results
                
        except Exception as e:
            logger.error(
                "search_failed",
                query=query[:50],
                error=str(e),
            )
            return []
    
    def search_all_channels(
        self,
        query: str,
        category_ids_exclude: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[SearchResult]:
        """
        Search across all channels.
        
        Args:
            query: Search query
            category_ids_exclude: Categories to exclude
            limit: Max results
            
        Returns:
            Search results from all channels
        """
        return self.search(
            query=query,
            channel_id=None,
            category_ids_exclude=category_ids_exclude,
            limit=limit,
        )
    
    def get_channel_messages(
        self,
        channel_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[StoredMessage]:
        """
        Get messages from a channel.
        
        Args:
            channel_id: Channel ID
            limit: Max messages
            offset: Pagination offset
            
        Returns:
            List of messages
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM messages 
                WHERE channel_id = ?
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            """, (channel_id, limit, offset))
            
            rows = cursor.fetchall()
            
            return [
                StoredMessage(
                    message_id=row["message_id"],
                    channel_id=row["channel_id"],
                    channel_name=row["channel_name"],
                    guild_id=row["guild_id"],
                    category_id=row["category_id"],
                    author_id=row["author_id"],
                    author_name=row["author_name"],
                    author_display_name=row["author_display_name"],
                    author_roles=json.loads(row["author_roles"]) if row["author_roles"] else None,
                    content=row["content"],
                    timestamp=row["timestamp"],
                    url=row["url"],
                    attachments_count=row["attachments_count"],
                )
                for row in rows
            ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM messages")
            total_messages = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT channel_id) FROM messages")
            total_channels = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT author_id) FROM messages")
            total_authors = cursor.fetchone()[0]
            
            # Database file size
            db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
            
            return {
                "total_messages": total_messages,
                "total_channels": total_channels,
                "total_authors": total_authors,
                "database_size_mb": round(db_size / (1024 * 1024), 2),
            }
    
    def get_daily_stats(self, days: int = 1) -> Dict[str, Any]:
        """
        Get statistics for the previous day(s).
        
        Args:
            days: Number of previous days to analyze (1 = yesterday only)
            
        Returns:
            Dict with daily statistics
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Calculate date range
            from datetime import timedelta
            now = datetime.utcnow()
            start_date = (now - timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = (now - timedelta(days=1)).replace(hour=23, minute=59, second=59)
            
            # Format for SUBSTR comparison (ignore timezone suffix in stored timestamps)
            start_str = start_date.strftime("%Y-%m-%dT%H:%M:%S")
            end_str = end_date.strftime("%Y-%m-%dT%H:%M:%S")
            
            # Total messages in period
            cursor.execute(
                "SELECT COUNT(*) FROM messages WHERE SUBSTR(timestamp, 1, 19) >= ? AND SUBSTR(timestamp, 1, 19) <= ?",
                (start_str, end_str)
            )
            total_messages = cursor.fetchone()[0]
            
            # Unique channels
            cursor.execute(
                "SELECT COUNT(DISTINCT channel_id) FROM messages WHERE SUBSTR(timestamp, 1, 19) >= ? AND SUBSTR(timestamp, 1, 19) <= ?",
                (start_str, end_str)
            )
            total_channels = cursor.fetchone()[0]
            
            # Unique authors
            cursor.execute(
                "SELECT COUNT(DISTINCT author_id) FROM messages WHERE SUBSTR(timestamp, 1, 19) >= ? AND SUBSTR(timestamp, 1, 19) <= ?",
                (start_str, end_str)
            )
            total_authors = cursor.fetchone()[0]
            
            # Top authors (spammers)
            cursor.execute(
                """
                SELECT author_id, author_name, author_display_name, COUNT(*) as msg_count
                FROM messages 
                WHERE SUBSTR(timestamp, 1, 19) >= ? AND SUBSTR(timestamp, 1, 19) <= ?
                GROUP BY author_id
                ORDER BY msg_count DESC
                LIMIT 10
                """,
                (start_str, end_str)
            )
            top_authors = [
                {
                    "author_id": row[0],
                    "author_name": row[1],
                    "author_display_name": row[2],
                    "message_count": row[3],
                }
                for row in cursor.fetchall()
            ]
            
            # Top channels
            cursor.execute(
                """
                SELECT channel_id, channel_name, COUNT(*) as msg_count
                FROM messages 
                WHERE SUBSTR(timestamp, 1, 19) >= ? AND SUBSTR(timestamp, 1, 19) <= ?
                GROUP BY channel_id
                ORDER BY msg_count DESC
                LIMIT 10
                """,
                (start_str, end_str)
            )
            top_channels = [
                {
                    "channel_id": row[0],
                    "channel_name": row[1],
                    "message_count": row[2],
                }
                for row in cursor.fetchall()
            ]
            
            return {
                "total_messages": total_messages,
                "total_channels": total_channels,
                "total_authors": total_authors,
                "top_authors": top_authors,
                "top_channels": top_channels,
                "start_date": start_str,
                "end_date": end_str,
            }
    
    def get_user_message_count(self, user_id: str) -> int:
        """Get total message count for a user."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM messages WHERE author_id = ?",
                (user_id,)
            )
            return cursor.fetchone()[0]
    
    def get_user_message_count_in_range(
        self, 
        user_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> int:
        """Get message count for a user in a date range."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Use SUBSTR to compare only datetime part (ignore timezone suffix)
            # Stored format: 2025-11-25T06:35:41.930000+00:00
            # Query format: 2025-11-25T06:35:41
            start_str = start_date.strftime("%Y-%m-%dT%H:%M:%S")
            end_str = end_date.strftime("%Y-%m-%dT%H:%M:%S")
            cursor.execute(
                """
                SELECT COUNT(*) FROM messages 
                WHERE author_id = ? 
                AND SUBSTR(timestamp, 1, 19) >= ? 
                AND SUBSTR(timestamp, 1, 19) <= ?
                """,
                (user_id, start_str, end_str)
            )
            return cursor.fetchone()[0]
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get detailed stats for a user."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Total messages
            cursor.execute(
                "SELECT COUNT(*) FROM messages WHERE author_id = ?",
                (user_id,)
            )
            total_messages = cursor.fetchone()[0]
            
            # Unique channels
            cursor.execute(
                "SELECT COUNT(DISTINCT channel_id) FROM messages WHERE author_id = ?",
                (user_id,)
            )
            channels_active = cursor.fetchone()[0]
            
            # First and last message
            cursor.execute(
                "SELECT MIN(timestamp), MAX(timestamp) FROM messages WHERE author_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            first_message = row[0]
            last_message = row[1]
            
            # Average message length
            cursor.execute(
                "SELECT AVG(LENGTH(content)) FROM messages WHERE author_id = ?",
                (user_id,)
            )
            avg_length = cursor.fetchone()[0] or 0
            
            return {
                "total_messages": total_messages,
                "channels_active": channels_active,
                "first_message": first_message,
                "last_message": last_message,
                "avg_message_length": int(avg_length),
            }
    
    def get_user_tweets(
        self, 
        user_id: str, 
        channel_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get user's messages containing x.com links.
        
        Args:
            user_id: User ID
            channel_id: Optional channel ID to filter
            limit: Max results
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if channel_id:
                cursor.execute(
                    """
                    SELECT message_id, content, url, timestamp, channel_name
                    FROM messages 
                    WHERE author_id = ? AND channel_id = ? AND content LIKE '%x.com%'
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (user_id, channel_id, limit)
                )
            else:
                cursor.execute(
                    """
                    SELECT message_id, content, url, timestamp, channel_name
                    FROM messages 
                    WHERE author_id = ? AND content LIKE '%x.com%'
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (user_id, limit)
                )
            
            return [
                {
                    "message_id": row[0],
                    "content": row[1],
                    "url": row[2],
                    "timestamp": row[3],
                    "channel_name": row[4],
                }
                for row in cursor.fetchall()
            ]
    
    def delete_channel_messages(self, channel_id: str) -> int:
        """
        Delete all messages from a channel.
        
        Args:
            channel_id: Channel ID
            
        Returns:
            Number of deleted messages
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM messages WHERE channel_id = ?",
                (channel_id,)
            )
            deleted = cursor.rowcount
            
            logger.info(
                "channel_messages_deleted",
                channel_id=channel_id,
                deleted=deleted,
            )
            
            return deleted


# Singleton instance
_storage_instance: Optional[SQLiteMessageStorage] = None


def get_message_storage(db_path: Optional[Path] = None) -> SQLiteMessageStorage:
    """
    Get singleton SQLite storage instance.
    
    Args:
        db_path: Optional database path (only used on first call)
        
    Returns:
        SQLiteMessageStorage instance
    """
    global _storage_instance
    
    if _storage_instance is None:
        _storage_instance = SQLiteMessageStorage(db_path)
    
    return _storage_instance
