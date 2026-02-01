"""
SQLite storage for content submission system (anti-slop).

Stores submissions, votes, decisions, blacklisted content IDs, and cooldowns.
"""

import sqlite3
import hashlib
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from contextlib import contextmanager
from enum import Enum

from src.utils import get_logger

logger = get_logger(__name__)

DEFAULT_DB_PATH = Path("data/messages.db")


class SubmissionStatus(Enum):
    """Status of a content submission."""
    PENDING = "pending"
    APPROVED = "approved"
    NEEDS_REVISION = "needs_revision"
    REJECTED = "rejected"
    EXPIRED = "expired"


class VoteType(Enum):
    """Vote types for submissions."""
    KEEP = "keep"       # 🟢
    REVISE = "revise"   # 🟡
    SLOP = "slop"       # 🔴


@dataclass
class Submission:
    """Content submission data."""
    id: int
    content_id: str
    message_id: str
    channel_id: str
    guild_path: str
    author_id: str
    author_name: str
    content: str
    attachment_urls: str
    status: str
    decision_by: Optional[str]
    decision_reason: Optional[str]
    revision_count: int
    original_submission_id: Optional[int]
    created_at: str
    decided_at: Optional[str]
    expires_at: str
    forwarded_message_id: Optional[str]


@dataclass
class Vote:
    """Vote on a submission."""
    id: int
    submission_id: int
    voter_id: str
    voter_name: str
    vote_type: str
    created_at: str


@dataclass
class Cooldown:
    """User cooldown for submissions."""
    user_id: str
    guild_path: str
    cooldown_until: str
    reason: str


class SubmissionStorage:
    """
    SQLite storage for content submission system.
    
    Tables:
    - submissions: All content submissions
    - submission_votes: T1+ member votes
    - blacklisted_content: Rejected content IDs (cannot resubmit)
    - user_cooldowns: Submission cooldowns after repeated slop
    - spotlight_content: Guild-lead curated exceptional work
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize submission storage."""
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_tables()
    
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
    
    def _init_tables(self):
        """Initialize database tables for submission system."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Content submissions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_id TEXT NOT NULL,
                    message_id TEXT UNIQUE NOT NULL,
                    channel_id TEXT NOT NULL,
                    guild_path TEXT NOT NULL,
                    author_id TEXT NOT NULL,
                    author_name TEXT NOT NULL,
                    content TEXT NOT NULL,
                    attachment_urls TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    decision_by TEXT,
                    decision_reason TEXT,
                    revision_count INTEGER DEFAULT 0,
                    original_submission_id INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    decided_at TEXT,
                    expires_at TEXT NOT NULL,
                    forwarded_message_id TEXT,
                    FOREIGN KEY (original_submission_id) REFERENCES submissions(id)
                )
            """)
            
            # Votes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS submission_votes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    submission_id INTEGER NOT NULL,
                    voter_id TEXT NOT NULL,
                    voter_name TEXT NOT NULL,
                    vote_type TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(submission_id, voter_id),
                    FOREIGN KEY (submission_id) REFERENCES submissions(id)
                )
            """)
            
            # Blacklisted content IDs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blacklisted_content (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_id TEXT UNIQUE NOT NULL,
                    original_author_id TEXT NOT NULL,
                    reason TEXT,
                    blacklisted_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    blacklisted_by TEXT
                )
            """)
            
            # User cooldowns
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_cooldowns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    guild_path TEXT NOT NULL,
                    cooldown_until TEXT NOT NULL,
                    reason TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, guild_path)
                )
            """)
            
            # Spotlight content
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS spotlight_content (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    submission_id INTEGER NOT NULL,
                    spotlighted_by TEXT NOT NULL,
                    spotlighted_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    spotlight_message_id TEXT,
                    FOREIGN KEY (submission_id) REFERENCES submissions(id)
                )
            """)
            
            # User submission stats (for tracking repeated slop)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_submission_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    guild_path TEXT NOT NULL,
                    total_submissions INTEGER DEFAULT 0,
                    approved_count INTEGER DEFAULT 0,
                    revision_count INTEGER DEFAULT 0,
                    rejected_count INTEGER DEFAULT 0,
                    consecutive_rejections INTEGER DEFAULT 0,
                    last_submission_at TEXT,
                    UNIQUE(user_id, guild_path)
                )
            """)
            
            # Indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_submissions_status ON submissions(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_submissions_author ON submissions(author_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_submissions_content_id ON submissions(content_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_submissions_expires ON submissions(expires_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_votes_submission ON submission_votes(submission_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_blacklist_content ON blacklisted_content(content_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cooldowns_user ON user_cooldowns(user_id)")
    
    @staticmethod
    def generate_content_id(content: str, attachment_urls: List[str] = None) -> str:
        """
        Generate unique content ID from content + attachments.
        Used to prevent resubmission of rejected content.
        """
        combined = content.strip().lower()
        if attachment_urls:
            combined += "|".join(sorted(attachment_urls))
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    # ==================== Submissions ====================
    
    def create_submission(
        self,
        message_id: str,
        channel_id: str,
        guild_path: str,
        author_id: str,
        author_name: str,
        content: str,
        attachment_urls: List[str] = None,
        expires_hours: int = 24,
        original_submission_id: int = None,
    ) -> Optional[Submission]:
        """Create a new content submission."""
        content_id = self.generate_content_id(content, attachment_urls)
        
        # Check if content is blacklisted
        if self.is_content_blacklisted(content_id):
            logger.warning("submission_blacklisted", content_id=content_id, author_id=author_id)
            return None
        
        expires_at = (datetime.utcnow() + timedelta(hours=expires_hours)).isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get revision count if this is a revision
            revision_count = 0
            if original_submission_id:
                cursor.execute(
                    "SELECT revision_count FROM submissions WHERE id = ?",
                    (original_submission_id,)
                )
                row = cursor.fetchone()
                if row:
                    revision_count = row["revision_count"] + 1
            
            cursor.execute("""
                INSERT INTO submissions (
                    content_id, message_id, channel_id, guild_path,
                    author_id, author_name, content, attachment_urls,
                    status, revision_count, original_submission_id, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                content_id, message_id, channel_id, guild_path,
                author_id, author_name, content,
                json.dumps(attachment_urls or []),
                SubmissionStatus.PENDING.value,
                revision_count,
                original_submission_id,
                expires_at,
            ))
            
            submission_id = cursor.lastrowid
            
            # Update user stats
            self._update_user_stats(cursor, author_id, guild_path, "submission")
            
            logger.info(
                "submission_created",
                submission_id=submission_id,
                content_id=content_id,
                author_id=author_id,
                guild_path=guild_path,
            )
            
            return self.get_submission(submission_id)
    
    def get_submission(self, submission_id: int) -> Optional[Submission]:
        """Get submission by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM submissions WHERE id = ?", (submission_id,))
            row = cursor.fetchone()
            if row:
                return Submission(**dict(row))
            return None
    
    def get_submission_by_message(self, message_id: str) -> Optional[Submission]:
        """Get submission by Discord message ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM submissions WHERE message_id = ?", (message_id,))
            row = cursor.fetchone()
            if row:
                return Submission(**dict(row))
            return None
    
    def get_pending_submissions(self, guild_path: str = None) -> List[Submission]:
        """Get all pending submissions, optionally filtered by guild path."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if guild_path:
                cursor.execute(
                    "SELECT * FROM submissions WHERE status = ? AND guild_path = ? ORDER BY created_at",
                    (SubmissionStatus.PENDING.value, guild_path)
                )
            else:
                cursor.execute(
                    "SELECT * FROM submissions WHERE status = ? ORDER BY created_at",
                    (SubmissionStatus.PENDING.value,)
                )
            return [Submission(**dict(row)) for row in cursor.fetchall()]
    
    def get_expired_submissions(self) -> List[Submission]:
        """Get submissions that have expired without a decision."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()
            cursor.execute(
                "SELECT * FROM submissions WHERE status = ? AND expires_at < ?",
                (SubmissionStatus.PENDING.value, now)
            )
            return [Submission(**dict(row)) for row in cursor.fetchall()]
    
    def decide_submission(
        self,
        submission_id: int,
        status: SubmissionStatus,
        decision_by: str,
        reason: str = None,
        forwarded_message_id: str = None,
    ) -> bool:
        """Record a decision on a submission."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get submission first
            cursor.execute("SELECT * FROM submissions WHERE id = ?", (submission_id,))
            row = cursor.fetchone()
            if not row:
                return False
            
            submission = Submission(**dict(row))
            
            cursor.execute("""
                UPDATE submissions
                SET status = ?, decision_by = ?, decision_reason = ?,
                    decided_at = ?, forwarded_message_id = ?
                WHERE id = ?
            """, (
                status.value, decision_by, reason,
                datetime.utcnow().isoformat(), forwarded_message_id,
                submission_id
            ))
            
            # Update user stats based on decision
            if status == SubmissionStatus.APPROVED:
                self._update_user_stats(cursor, submission.author_id, submission.guild_path, "approved")
            elif status == SubmissionStatus.NEEDS_REVISION:
                self._update_user_stats(cursor, submission.author_id, submission.guild_path, "revision")
            elif status == SubmissionStatus.REJECTED:
                self._update_user_stats(cursor, submission.author_id, submission.guild_path, "rejected")
                # Blacklist the content
                self.blacklist_content(
                    submission.content_id,
                    submission.author_id,
                    reason or "Rejected as slop",
                    decision_by,
                )
            
            logger.info(
                "submission_decided",
                submission_id=submission_id,
                status=status.value,
                decision_by=decision_by,
            )
            
            return True
    
    def update_forwarded_message(self, submission_id: int, forwarded_message_id: str) -> bool:
        """Update the forwarded message ID for an approved submission."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE submissions SET forwarded_message_id = ? WHERE id = ?",
                (forwarded_message_id, submission_id)
            )
            return cursor.rowcount > 0
    
    # ==================== Votes ====================
    
    def add_vote(
        self,
        submission_id: int,
        voter_id: str,
        voter_name: str,
        vote_type: VoteType,
    ) -> bool:
        """Add or update a vote on a submission."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO submission_votes
                (submission_id, voter_id, voter_name, vote_type, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                submission_id, voter_id, voter_name,
                vote_type.value, datetime.utcnow().isoformat()
            ))
            return True
    
    def remove_vote(self, submission_id: int, voter_id: str) -> bool:
        """Remove a vote from a submission."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM submission_votes WHERE submission_id = ? AND voter_id = ?",
                (submission_id, voter_id)
            )
            return cursor.rowcount > 0
    
    def get_votes(self, submission_id: int) -> Dict[str, List[Vote]]:
        """Get all votes for a submission, grouped by type."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM submission_votes WHERE submission_id = ?",
                (submission_id,)
            )
            votes = {"keep": [], "revise": [], "slop": []}
            for row in cursor.fetchall():
                vote = Vote(**dict(row))
                votes[vote.vote_type].append(vote)
            return votes
    
    def get_vote_summary(self, submission_id: int) -> Dict[str, int]:
        """Get vote counts for a submission."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT vote_type, COUNT(*) as count
                FROM submission_votes
                WHERE submission_id = ?
                GROUP BY vote_type
            """, (submission_id,))
            
            summary = {"keep": 0, "revise": 0, "slop": 0}
            for row in cursor.fetchall():
                summary[row["vote_type"]] = row["count"]
            return summary
    
    # ==================== Blacklist ====================
    
    def blacklist_content(
        self,
        content_id: str,
        author_id: str,
        reason: str,
        blacklisted_by: str,
    ) -> bool:
        """Add content ID to blacklist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO blacklisted_content
                    (content_id, original_author_id, reason, blacklisted_by)
                    VALUES (?, ?, ?, ?)
                """, (content_id, author_id, reason, blacklisted_by))
                logger.info("content_blacklisted", content_id=content_id)
                return True
            except sqlite3.IntegrityError:
                return False  # Already blacklisted
    
    def is_content_blacklisted(self, content_id: str) -> bool:
        """Check if content ID is blacklisted."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM blacklisted_content WHERE content_id = ?",
                (content_id,)
            )
            return cursor.fetchone() is not None
    
    # ==================== Cooldowns ====================
    
    def set_cooldown(
        self,
        user_id: str,
        guild_path: str,
        hours: int,
        reason: str = None,
    ) -> datetime:
        """Set a cooldown for a user in a guild path."""
        cooldown_until = datetime.utcnow() + timedelta(hours=hours)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO user_cooldowns
                (user_id, guild_path, cooldown_until, reason)
                VALUES (?, ?, ?, ?)
            """, (user_id, guild_path, cooldown_until.isoformat(), reason))
        
        logger.info(
            "cooldown_set",
            user_id=user_id,
            guild_path=guild_path,
            hours=hours,
        )
        return cooldown_until
    
    def get_cooldown(self, user_id: str, guild_path: str) -> Optional[datetime]:
        """Get cooldown end time for a user. Returns None if no active cooldown."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT cooldown_until FROM user_cooldowns WHERE user_id = ? AND guild_path = ?",
                (user_id, guild_path)
            )
            row = cursor.fetchone()
            if row:
                cooldown_until = datetime.fromisoformat(row["cooldown_until"])
                if cooldown_until > datetime.utcnow():
                    return cooldown_until
                # Cooldown expired, clean up
                cursor.execute(
                    "DELETE FROM user_cooldowns WHERE user_id = ? AND guild_path = ?",
                    (user_id, guild_path)
                )
            return None
    
    def clear_cooldown(self, user_id: str, guild_path: str) -> bool:
        """Clear cooldown for a user."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM user_cooldowns WHERE user_id = ? AND guild_path = ?",
                (user_id, guild_path)
            )
            return cursor.rowcount > 0
    
    # ==================== Spotlight ====================
    
    def add_to_spotlight(
        self,
        submission_id: int,
        spotlighted_by: str,
        spotlight_message_id: str = None,
    ) -> bool:
        """Add a submission to spotlight."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO spotlight_content
                    (submission_id, spotlighted_by, spotlight_message_id)
                    VALUES (?, ?, ?)
                """, (submission_id, spotlighted_by, spotlight_message_id))
                logger.info("submission_spotlighted", submission_id=submission_id)
                return True
            except sqlite3.IntegrityError:
                return False
    
    def get_spotlight_submissions(self, limit: int = 10) -> List[Dict]:
        """Get recent spotlight submissions with full details."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*, sp.spotlighted_by, sp.spotlighted_at, sp.spotlight_message_id
                FROM spotlight_content sp
                JOIN submissions s ON sp.submission_id = s.id
                ORDER BY sp.spotlighted_at DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== User Stats ====================
    
    def _update_user_stats(
        self,
        cursor: sqlite3.Cursor,
        user_id: str,
        guild_path: str,
        action: str,
    ):
        """Update user submission statistics."""
        # Ensure row exists
        cursor.execute("""
            INSERT OR IGNORE INTO user_submission_stats
            (user_id, guild_path, total_submissions, approved_count, 
             revision_count, rejected_count, consecutive_rejections)
            VALUES (?, ?, 0, 0, 0, 0, 0)
        """, (user_id, guild_path))
        
        if action == "submission":
            cursor.execute("""
                UPDATE user_submission_stats
                SET total_submissions = total_submissions + 1,
                    last_submission_at = ?
                WHERE user_id = ? AND guild_path = ?
            """, (datetime.utcnow().isoformat(), user_id, guild_path))
        
        elif action == "approved":
            cursor.execute("""
                UPDATE user_submission_stats
                SET approved_count = approved_count + 1,
                    consecutive_rejections = 0
                WHERE user_id = ? AND guild_path = ?
            """, (user_id, guild_path))
        
        elif action == "revision":
            cursor.execute("""
                UPDATE user_submission_stats
                SET revision_count = revision_count + 1
                WHERE user_id = ? AND guild_path = ?
            """, (user_id, guild_path))
        
        elif action == "rejected":
            cursor.execute("""
                UPDATE user_submission_stats
                SET rejected_count = rejected_count + 1,
                    consecutive_rejections = consecutive_rejections + 1
                WHERE user_id = ? AND guild_path = ?
            """, (user_id, guild_path))
    
    def get_user_stats(self, user_id: str, guild_path: str = None) -> Dict:
        """Get user submission statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if guild_path:
                cursor.execute(
                    "SELECT * FROM user_submission_stats WHERE user_id = ? AND guild_path = ?",
                    (user_id, guild_path)
                )
                row = cursor.fetchone()
                return dict(row) if row else {}
            else:
                cursor.execute(
                    "SELECT * FROM user_submission_stats WHERE user_id = ?",
                    (user_id,)
                )
                return [dict(row) for row in cursor.fetchall()]
    
    def get_consecutive_rejections(self, user_id: str, guild_path: str) -> int:
        """Get consecutive rejection count for cooldown calculation."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT consecutive_rejections FROM user_submission_stats WHERE user_id = ? AND guild_path = ?",
                (user_id, guild_path)
            )
            row = cursor.fetchone()
            return row["consecutive_rejections"] if row else 0
    
    # ==================== Analytics ====================
    
    def get_user_approved_content(self, user_id: str, limit: int = 50) -> List[Submission]:
        """Get user's approved submissions (for portfolio)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM submissions
                WHERE author_id = ? AND status = ?
                ORDER BY decided_at DESC
                LIMIT ?
            """, (user_id, SubmissionStatus.APPROVED.value, limit))
            return [Submission(**dict(row)) for row in cursor.fetchall()]
    
    def get_guild_stats(self, guild_path: str) -> Dict:
        """Get statistics for a guild path."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved,
                    SUM(CASE WHEN status = 'needs_revision' THEN 1 ELSE 0 END) as revisions,
                    SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending
                FROM submissions
                WHERE guild_path = ?
            """, (guild_path,))
            
            row = cursor.fetchone()
            return dict(row) if row else {}


# Singleton instance
_submission_storage: Optional[SubmissionStorage] = None


def get_submission_storage() -> SubmissionStorage:
    """Get singleton submission storage instance."""
    global _submission_storage
    if _submission_storage is None:
        _submission_storage = SubmissionStorage()
    return _submission_storage
