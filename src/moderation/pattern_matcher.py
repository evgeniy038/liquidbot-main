"""
Pattern-based scam detection using keywords and regex.
"""

import re
from typing import Dict, List, Set
from dataclasses import dataclass

from src.utils import get_logger

logger = get_logger(__name__)


@dataclass
class PatternMatch:
    """Result of pattern matching."""
    matched: bool
    score: int
    matched_patterns: List[str]
    matched_keywords: List[str]


class PatternMatcher:
    """
    Fast pattern-based scam detection.
    
    Uses keywords and regex patterns to identify suspicious content.
    """
    
    def __init__(
        self,
        keywords: List[str],
        regex_patterns: List[str],
        url_whitelist: List[str] = None,
    ):
        """
        Initialize pattern matcher.
        
        Args:
            keywords: List of suspicious keywords
            regex_patterns: List of regex patterns
            url_whitelist: List of trusted domains to ignore
        """
        self.keywords = [kw.lower() for kw in keywords]
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in regex_patterns
        ]
        self.url_whitelist = [domain.lower() for domain in (url_whitelist or [])]
        
        logger.info(
            "pattern_matcher_initialized",
            keywords_count=len(self.keywords),
            patterns_count=len(self.compiled_patterns),
            whitelisted_domains=len(self.url_whitelist),
        )
        
        # Pre-compute normalized keywords for faster checking
        # Remove non-alphanumeric chars from keywords: "discord.gg" -> "discordgg"
        self.normalized_keywords = []
        for kw in self.keywords:
            clean_kw = re.sub(r'[^a-z0-9]', '', kw)
            if len(clean_kw) > 3:  # Only normalize if substantial enough to avoid false positives
                self.normalized_keywords.append(clean_kw)
    
    def check_message(self, content: str) -> PatternMatch:
        """
        Check message content for suspicious patterns.
        
        Args:
            content: Message content to check
        
        Returns:
            PatternMatch with results
        """
        content_lower = content.lower()
        
        # Check if message contains only whitelisted URLs
        urls = self.extract_urls(content)
        if urls and self._all_urls_whitelisted(urls):
            logger.debug(
                "all_urls_whitelisted",
                urls_count=len(urls),
            )
            # Still check for keywords, but reduce score
            score_multiplier = 0.5  # Reduce score if URLs are trusted
        else:
            score_multiplier = 1.0
        
        matched_keywords = []
        matched_patterns = []
        score = 0
        
        # Check keywords
        for keyword in self.keywords:
            if keyword in content_lower:
                matched_keywords.append(keyword)
                score += int(10 * score_multiplier)  # Each keyword adds 10 points (or 5 if whitelisted URLs)
        
        # Check regex patterns (higher weight because more accurate)
        for pattern in self.compiled_patterns:
            if pattern.search(content):
                matched_patterns.append(pattern.pattern)
                score += int(20 * score_multiplier)  # Each pattern adds 20 points (or 10 if whitelisted URLs)
        
        matched = len(matched_keywords) > 0 or len(matched_patterns) > 0
        
        if matched:
            logger.debug(
                "patterns_matched",
                score=score,
                keywords=matched_keywords,
                patterns=matched_patterns,
                score_multiplier=score_multiplier,
            )
            
        # If no match yet (or even if matched), check normalized content for obfuscation
        # This catches "d i s c o r d . g g" or "d.i.s.c.o.r.d"
        if not matched or score < 100:  # Continue if score isn't already very high
            normalized_content = self._normalize_content(content)
            
            # Check normalized keywords
            for i, norm_kw in enumerate(self.normalized_keywords):
                if norm_kw in normalized_content:
                    # Map back to original keyword for reporting
                    original_kw = self.keywords[i] if i < len(self.keywords) else norm_kw
                    
                    if original_kw not in matched_keywords:
                        matched_keywords.append(f"{original_kw}(hidden)")
                        score += int(15 * score_multiplier) # Slightly higher than normal keyword
                        matched = True
                        
            if matched:
                 logger.debug(
                    "patterns_matched_normalized",
                    score=score,
                    keywords=matched_keywords,
                )
        
        return PatternMatch(
            matched=matched,
            score=score,
            matched_patterns=matched_patterns,
            matched_keywords=matched_keywords,
        )
    
    def _all_urls_whitelisted(self, urls: List[str]) -> bool:
        """
        Check if all URLs in list are from whitelisted domains.
        
        Args:
            urls: List of URLs
        
        Returns:
            True if all URLs are whitelisted
        """
        if not urls:
            return False
        
        domains = self.extract_domains_from_urls(urls)
        
        for domain in domains:
            domain_lower = domain.lower()
            # Check if domain or any parent domain is whitelisted
            is_whitelisted = False
            for whitelisted in self.url_whitelist:
                if whitelisted in domain_lower or domain_lower.endswith(whitelisted):
                    is_whitelisted = True
                    break
            
            if not is_whitelisted:
                return False
        
        return True
    
    def extract_domains_from_urls(self, urls: List[str]) -> List[str]:
        """
        Extract domain names from list of URLs.
        
        Args:
            urls: List of URLs
        
        Returns:
            List of domain names
        """
        domains = []
        domain_pattern = re.compile(r'https?://([^/]+)')
        
        for url in urls:
            match = domain_pattern.search(url)
            if match:
                domains.append(match.group(1))
        
        return domains
    
    def extract_urls(self, content: str) -> List[str]:
        """
        Extract URLs from message content.
        
        Args:
            content: Message content
        
        Returns:
            List of found URLs
        """
        url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        
        urls = url_pattern.findall(content)
        return urls
    
    def extract_domains(self, content: str) -> List[str]:
        """
        Extract domain names from URLs in content.
        
        Args:
            content: Message content
        
        Returns:
            List of domain names
        """
        urls = self.extract_urls(content)
        domains = []
        
        domain_pattern = re.compile(r'https?://([^/]+)')
        
        for url in urls:
            match = domain_pattern.search(url)
            if match:
                domains.append(match.group(1))
        
        return domains
        return domains

    def _normalize_content(self, content: str) -> str:
        """
        Normalize content by removing all non-alphanumeric characters.
        
        Args:
            content: Message content
            
        Returns:
            Normalized content (only a-z0-9)
        """
        # Remove all non-alphanumeric characters
        return re.sub(r'[^a-zA-Z0-9]', '', content).lower()
