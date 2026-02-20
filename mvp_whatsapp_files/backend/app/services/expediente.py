"""Expediente generation service for creating ZIP files with client documents."""
import io
import re
import zipfile
from typing import List, Tuple
from uuid import UUID

from app.adapters.factory import get_repository, get_storage
from app.core.logging import get_logger
from app.models.enums import DocumentType

logger = get_logger(__name__)


def sanitize_name(name: str) -> str:
    """
    Sanitize client name for use in filenames and folder names.
    
    Rules:
    - Replace spaces with underscores
    - Remove special characters (keep only alphanumeric, underscore, hyphen)
    - Convert to lowercase for consistency
    
    Args:
        name: Client full name
        
    Returns:
        Sanitized name safe for filenames
    """
    # Replace spaces with underscores
    sanitized = name.replace(" ", "_")
    
    # Remove special characters, keep alphanumeric, underscore, hyphen
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', sanitized)
    
    # Convert to lowercase for consistency
    sanitized = sanitized.lower()
    
    return sanitized


def detect_nie(passport_or_nie: str) -> bool:
    """
    Detect if the passport/NIE field contains a Spanish NIE.
    
    NIE format: ^[XYZxyz]\d{7}[A-Za-z]$
    - Starts with X, Y, or Z (case insensitive)
    - Followed by 7 digits
    - Ends with a letter
    
    Args:
        passport_or_nie: Client's passport number or NIE
        
    Returns:
        True if matches NIE pattern, False otherwise
    """
    nie_pattern = r'^[XYZxyz]\d{7}[A-Za-z]$'
    return bool(re.match(nie_pattern, passport_or_nie.strip()))


def get_document_label(passport_or_nie: str) -> str:
    """
    Get the document label based on NIE detection.
    
    Args:
        passport_or_nie: Client's passport number or NIE
        
    Returns:
        "NIE" if it's a Spanish NIE, "Pasaporte" otherwise
    """
    return "NIE" if detect_nie(passport_or_nie) else "Pasaporte"


class MissingDocumentsError(Exception):
    """Exception raised when required documents are missing."""
    
    def __init__(self, missing: List[str]):
        self.missing = missing
        super().__init__(f"Missing required documents: {', '.join(missing)}")


def generate_expediente_zip(client_id: UUID, accepted_only: bool = False) -> Tuple[bytes, str]:
    """
    Generate a ZIP file containing all required documents for a client.
    
    The ZIP structure:
    - Folder name: {sanitized_name}_{client_id_short}/
    - Files inside:
      * Tasa_{sanitized_name}.pdf (TASA document)
      * {NIE|Pasaporte}_{sanitized_name}.pdf (PASSPORT_NIE document)
    
    Args:
        client_id: UUID of the client
        
    Returns:
        Tuple of (zip_bytes, folder_name)
        
    Raises:
        ValueError: If client not found
        MissingDocumentsError: If required documents are missing
    """
    repository = get_repository()
    storage = get_storage()
    
    # Fetch client
    client = repository.get_client_by_id(client_id)
    if not client:
        raise ValueError(f"Client {client_id} not found")
    
    # Validate passport_or_nie exists
    passport_or_nie = client.get("passport_or_nie")
    if not passport_or_nie:
        raise MissingDocumentsError(["passport_or_nie field"])
    
    # Fetch all client documents
    documents = repository.get_client_documents(client_id)
    
    def is_accepted(doc: dict) -> bool:
        return (doc.get("metadata") or {}).get("review_status") == "accepted"

    # Find required documents (latest by uploaded_at from repository ordering).
    tasa_doc = None
    passport_nie_doc = None

    for doc in documents:
        doc_type = doc.get("document_type")
        if accepted_only and not is_accepted(doc):
            continue
        if doc_type == DocumentType.TASA.value and tasa_doc is None:
            tasa_doc = doc
        elif doc_type == DocumentType.PASSPORT_NIE.value and passport_nie_doc is None:
            passport_nie_doc = doc

    # Check for missing documents
    missing = []
    if not tasa_doc:
        missing.append("TASA_ACCEPTED" if accepted_only else "TASA")
    if not passport_nie_doc:
        missing.append("PASSPORT_NIE_ACCEPTED" if accepted_only else "PASSPORT_NIE")
    
    if missing:
        raise MissingDocumentsError(missing)
    
    # Prepare folder and ZIP name
    client_name = client.get("name", "Unknown")
    sanitized_name = sanitize_name(client_name)
    sanitized_passport = sanitize_name(passport_or_nie)  # Sanitize passport/NIE
    folder_name = f"{sanitized_name}_{sanitized_passport}"
    zip_name = f"{folder_name}.zip"  # ZIP file must have same name as folder + .zip
    
    # Determine document label
    doc_label = get_document_label(passport_or_nie)
    
    # Create ZIP in memory
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Download and add TASA document
        tasa_path = tasa_doc.get("storage_path")
        
        try:
            # Read TASA file from storage
            tasa_content = _download_file_from_storage(storage, tasa_path)
            tasa_filename = f"Tasa_{sanitized_name}.pdf"
            zip_file.writestr(f"{folder_name}/{tasa_filename}", tasa_content)
            logger.info(f"Added TASA document to ZIP: {tasa_filename}")
        except Exception as e:
            logger.error(f"Error adding TASA document: {e}")
            raise
        
        # Download and add PASSPORT_NIE document
        passport_nie_path = passport_nie_doc.get("storage_path")
        
        try:
            # Read PASSPORT_NIE file from storage
            passport_nie_content = _download_file_from_storage(storage, passport_nie_path)
            passport_nie_filename = f"{doc_label}_{sanitized_name}.pdf"
            zip_file.writestr(f"{folder_name}/{passport_nie_filename}", passport_nie_content)
            logger.info(f"Added {doc_label} document to ZIP: {passport_nie_filename}")
        except Exception as e:
            logger.error(f"Error adding {doc_label} document: {e}")
            raise
    
    zip_buffer.seek(0)
    zip_bytes = zip_buffer.read()
    
    logger.info(f"Generated expediente ZIP for client {client_id}: {zip_name} ({len(zip_bytes)} bytes)")
    
    # Return ZIP bytes and ZIP filename (without .zip extension for download endpoint)
    return zip_bytes, folder_name


def _download_file_from_storage(storage, file_path: str) -> bytes:
    """
    Download file content from storage.
    
    This is a helper function that abstracts the storage download logic.
    For Supabase, we need to use the SERVICE_ROLE_KEY to download files directly.
    
    Args:
        storage: Storage adapter instance
        file_path: Path to file in storage
        
    Returns:
        File content as bytes
    """
    # Get the Supabase client from storage
    supabase_client = storage.client
    
    # Download file from storage bucket
    response = supabase_client.client.storage.from_(supabase_client.bucket_name).download(file_path)
    
    return response
