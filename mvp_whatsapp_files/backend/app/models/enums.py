"""Enumeration types matching database schema."""
from enum import Enum


class ProfileType(str, Enum):
    """Client profile type enumeration."""
    ASYLUM = "ASYLUM"
    ARRAIGO = "ARRAIGO"
    STUDENT = "STUDENT"
    IRREGULAR = "IRREGULAR"
    OTHER = "OTHER"


class MessageDirection(str, Enum):
    """Message direction enumeration."""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class ClientStatus(str, Enum):
    """Client status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class DocumentType(str, Enum):
    """Document type enumeration for required client documents."""
    TASA = "TASA"
    PASSPORT_NIE = "PASSPORT_NIE"
