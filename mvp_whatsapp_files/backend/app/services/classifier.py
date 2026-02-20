"""Profile classification service."""
import re

from app.core.logging import get_logger
from app.models.enums import ProfileType

logger = get_logger(__name__)


def classify_profile(text: str) -> ProfileType:
    """
    Classify client profile type based on message content.
    
    Uses simple keyword-based rules for MVP:
    - "asilo" → ASYLUM
    - "arraigo" → ARRAIGO
    - "estudiante" → STUDENT
    - "irregular" → IRREGULAR
    - else → OTHER
    
    Args:
        text: Message text to analyze
        
    Returns:
        Classified profile type
    """
    if not text:
        return ProfileType.OTHER
    
    # Normalize text for matching
    text_lower = text.lower()
    
    # Keyword patterns (case-insensitive)
    patterns = {
        ProfileType.ASYLUM: r'\basilo\b',
        ProfileType.ARRAIGO: r'\barraigo\b',
        ProfileType.STUDENT: r'\bestudiante\b',
        ProfileType.IRREGULAR: r'\birregular\b',
    }
    
    # Check each pattern
    for profile_type, pattern in patterns.items():
        if re.search(pattern, text_lower):
            logger.info(f"Classified as {profile_type.value} based on keyword match")
            return profile_type
    
    logger.info("No keyword match, classified as OTHER")
    return ProfileType.OTHER
