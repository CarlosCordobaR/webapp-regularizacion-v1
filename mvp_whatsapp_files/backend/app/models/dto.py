"""Data Transfer Objects (DTOs) for API communication."""
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.enums import ClientStatus, DocumentType, MessageDirection, ProfileType


def validate_phone_number(phone: str) -> str:
    """Validate and normalize phone number.
    
    Rules:
    - Must contain 8-15 digits (excluding '+')
    - Can start with '+' (E.164 format)
    - Strips spaces and common separators
    
    Returns:
        Normalized phone number
        
    Raises:
        ValueError: If phone format is invalid
    """
    # Remove common separators and spaces
    cleaned = phone.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    
    # Check format: optional '+' followed by digits
    if not re.match(r'^\+?\d{8,15}$', cleaned):
        raise ValueError(
            "Invalid phone number format. Must contain 8-15 digits, "
            "optionally starting with '+' (e.g., +34600111222)"
        )
    
    return cleaned


# Client DTOs
class ClientBase(BaseModel):
    """Base client model."""
    phone_number: str
    name: Optional[str] = None
    profile_type: ProfileType = ProfileType.OTHER
    status: ClientStatus = ClientStatus.ACTIVE


class ClientCreate(ClientBase):
    """Client creation model."""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ClientCreateRequest(BaseModel):
    """Client creation request from API."""
    full_name: str = Field(..., min_length=1, max_length=255, description="Client full name")
    phone_number: str = Field(..., min_length=8, max_length=20, description="Client phone number (E.164 format preferred)")
    passport_or_nie: str = Field(..., min_length=1, max_length=50, description="Passport number or NIE (Spanish ID for foreigners)")
    email: Optional[str] = Field(default=None, max_length=255, description="Client email address")
    profile_type: ProfileType = Field(default=ProfileType.OTHER, description="Client profile type")
    status: ClientStatus = Field(default=ClientStatus.ACTIVE, description="Client status")
    notes: Optional[str] = Field(default=None, max_length=1000, description="Optional notes")
    
    @field_validator('phone_number')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate and normalize phone number."""
        return validate_phone_number(v)
    
    @field_validator('full_name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Trim and validate full name."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Full name cannot be empty")
        return stripped
    
    @field_validator('passport_or_nie')
    @classmethod
    def validate_passport_or_nie(cls, v: str) -> str:
        """Trim and validate passport or NIE."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Passport or NIE cannot be empty")
        return stripped


class ClientResponse(ClientBase):
    """Client response model."""
    id: UUID
    passport_or_nie: str
    email: Optional[str] = None
    notes: Optional[str] = None
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    document_count: Optional[int] = 0
    has_recent_conversation: Optional[bool] = False

    class Config:
        from_attributes = True


class ClientListResponse(BaseModel):
    """Paginated client list response."""
    data: List[ClientResponse]
    total: int
    page: int
    page_size: int


# Conversation DTOs
class ConversationBase(BaseModel):
    """Base conversation model."""
    message_id: str
    direction: MessageDirection
    content: Optional[str] = None
    message_type: str


class ConversationCreate(ConversationBase):
    """Conversation creation model."""
    client_id: UUID
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationResponse(ConversationBase):
    """Conversation response model."""
    id: UUID
    client_id: UUID
    metadata: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """Paginated conversation list response."""
    data: List[ConversationResponse]
    total: int
    page: int
    page_size: int


# Document DTOs
class DocumentBase(BaseModel):
    """Base document model."""
    storage_path: str
    original_filename: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    profile_type: Optional[ProfileType] = None
    document_type: Optional[DocumentType] = Field(default=None, description="Document type classification (TASA or PASSPORT_NIE)")


class DocumentCreate(DocumentBase):
    """Document creation model."""
    client_id: UUID
    conversation_id: Optional[UUID] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('document_type')
    @classmethod
    def validate_document_type(cls, v: Optional[DocumentType]) -> Optional[DocumentType]:
        """Validate document type if provided."""
        # Allow None for documents not part of expediente (e.g., conversation attachments)
        if v is not None and v not in [DocumentType.TASA, DocumentType.PASSPORT_NIE]:
            raise ValueError(f"Invalid document type. Must be one of: {[dt.value for dt in DocumentType]}")
        return v


class DocumentResponse(DocumentBase):
    """Document response model."""
    id: UUID
    client_id: UUID
    conversation_id: Optional[UUID] = None
    metadata: Dict[str, Any]
    uploaded_at: datetime
    public_url: Optional[str] = None

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Paginated document list response."""
    data: List[DocumentResponse]
    total: int
    page: int
    page_size: int


class SignedUrlResponse(BaseModel):
    """Signed URL response model."""
    url: str
    expires_in: int = 3600


# WhatsApp Webhook DTOs
class WhatsAppProfile(BaseModel):
    """WhatsApp profile information."""
    name: str


class WhatsAppContact(BaseModel):
    """WhatsApp contact information."""
    profile: WhatsAppProfile
    wa_id: str


class WhatsAppTextMessage(BaseModel):
    """WhatsApp text message."""
    body: str


class WhatsAppMediaMessage(BaseModel):
    """WhatsApp media/document message."""
    id: str
    mime_type: Optional[str] = None
    sha256: Optional[str] = None
    filename: Optional[str] = None
    caption: Optional[str] = None


class WhatsAppMessage(BaseModel):
    """WhatsApp message structure."""
    from_: str = Field(alias="from")
    id: str
    timestamp: str
    type: str
    text: Optional[WhatsAppTextMessage] = None
    document: Optional[WhatsAppMediaMessage] = None
    image: Optional[WhatsAppMediaMessage] = None
    audio: Optional[WhatsAppMediaMessage] = None
    video: Optional[WhatsAppMediaMessage] = None

    class Config:
        populate_by_name = True


class WhatsAppMetadata(BaseModel):
    """WhatsApp metadata."""
    display_phone_number: str
    phone_number_id: str


class WhatsAppConversationRef(BaseModel):
    """WhatsApp conversation metadata in status webhooks."""
    id: Optional[str] = None
    expiration_timestamp: Optional[str] = None
    origin: Optional[Dict[str, Any]] = None


class WhatsAppStatus(BaseModel):
    """WhatsApp outbound delivery/read status."""
    id: str
    status: str
    timestamp: Optional[str] = None
    recipient_id: Optional[str] = None
    conversation: Optional[WhatsAppConversationRef] = None
    errors: Optional[List[Dict[str, Any]]] = None


class WhatsAppValue(BaseModel):
    """WhatsApp value structure."""
    messaging_product: str
    metadata: WhatsAppMetadata
    contacts: Optional[List[WhatsAppContact]] = None
    messages: Optional[List[WhatsAppMessage]] = None
    statuses: Optional[List[WhatsAppStatus]] = None


class WhatsAppChange(BaseModel):
    """WhatsApp change structure."""
    value: WhatsAppValue
    field: str


class WhatsAppEntry(BaseModel):
    """WhatsApp entry structure."""
    id: str
    changes: List[WhatsAppChange]


class WhatsAppWebhook(BaseModel):
    """WhatsApp webhook payload."""
    object: str
    entry: List[WhatsAppEntry]
