"""Client management endpoints."""
import datetime
import hashlib
import json
from typing import Dict, List
from uuid import UUID
from fastapi import APIRouter, File, Form, Header, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.adapters.factory import get_repository, get_storage
from app.core.logging import get_logger
from app.models.dto import ClientListResponse, ClientResponse
from app.models.enums import ClientStatus, DocumentType, ProfileType
from app.services.expediente import MissingDocumentsError, generate_expediente_zip
from app.services.file_validation import validate_pdf_upload
from app.services.portal_auth import create_portal_token, token_expiration, verify_portal_token

logger = get_logger(__name__)
router = APIRouter(prefix="/clients", tags=["clients"])


class PortalAuthRequest(BaseModel):
    """Portal login request."""
    phone_number: str
    passport_or_nie: str


class ExportJobRequest(BaseModel):
    """Export request options."""
    accepted_only: bool = True
    expires_in: int = 3600
    requested_by: str = "staff"


def _portal_checklist(documents: List[Dict]) -> List[Dict]:
    required = [
        {"type": DocumentType.TASA.value, "label": "Comprobante TASA"},
        {"type": DocumentType.PASSPORT_NIE.value, "label": "Pasaporte / NIE"},
    ]

    def latest_doc(doc_type: str):
        typed = [d for d in documents if d.get("document_type") == doc_type]
        typed.sort(key=lambda x: x.get("uploaded_at", ""), reverse=True)
        return typed[0] if typed else None

    result = []
    for item in required:
        current = latest_doc(item["type"])
        if not current:
            result.append(
                {
                    "type": item["type"],
                    "label": item["label"],
                    "status": "missing",
                    "message": "Pendiente de carga.",
                }
            )
            continue

        review = (current.get("metadata") or {}).get("review_status")
        if review == "accepted":
            status_value = "accepted"
            message = "Documento validado por el equipo."
        elif review == "rejected":
            status_value = "rejected"
            note = (current.get("metadata") or {}).get("review_note")
            message = f"Rechazado: {note}" if note else "Rechazado por revisión."
        else:
            status_value = "uploaded"
            message = "Cargado y pendiente de revisión."

        result.append(
            {
                "type": item["type"],
                "label": item["label"],
                "status": status_value,
                "message": message,
                "document_id": current.get("id"),
                "uploaded_at": current.get("uploaded_at"),
            }
        )
    return result


def _register_document_version_and_audit(
    repository,
    *,
    client_id: UUID,
    document_id: str,
    document_type: str,
    storage_path: str,
    original_filename: str,
    mime_type: str,
    file_size: int,
    content_sha256: str,
    actor: str,
) -> dict:
    """Create a document version row and an audit event for typed uploads."""
    try:
        latest_version = repository.get_latest_document_version(client_id, document_type)
        version_number = (latest_version["version_number"] if latest_version else 0) + 1

        version = repository.create_document_version(
            {
                "client_id": str(client_id),
                "document_type": document_type,
                "document_id": document_id,
                "version_number": version_number,
                "content_sha256": content_sha256,
                "storage_path": storage_path,
                "original_filename": original_filename,
                "mime_type": mime_type,
                "file_size": file_size,
                "metadata": {"source": "webapp"},
            }
        )

        repository.create_audit_event(
            {
                "client_id": str(client_id),
                "event_type": "DOC_UPLOADED" if version_number == 1 else "DOC_REUPLOADED",
                "actor": actor,
                "details": {
                    "document_id": document_id,
                    "document_type": document_type,
                    "version_number": version_number,
                    "content_sha256": content_sha256,
                    "storage_path": storage_path,
                },
            }
        )

        return version
    except Exception as e:
        logger.warning(
            "Version/audit persistence unavailable for client=%s type=%s: %s",
            client_id,
            document_type,
            e,
        )
        return None


@router.get("", response_model=ClientListResponse)
async def list_clients(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """
    List all clients with pagination.
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        
    Returns:
        Paginated list of clients
    """
    repository = get_repository()
    
    try:
        clients, total = repository.get_clients(page=page, page_size=page_size)
        
        return ClientListResponse(
            data=[ClientResponse(**client) for client in clients],
            total=total,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        logger.error(f"Error listing clients: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch clients")


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(client_id: UUID):
    """
    Get client details by ID.
    
    Args:
        client_id: Client UUID
        
    Returns:
        Client details
    """
    repository = get_repository()
    
    client = repository.get_client_by_id(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return ClientResponse(**client)


@router.post("/{client_id}/portal-auth")
async def portal_auth(client_id: UUID, request: PortalAuthRequest):
    """
    Authenticate a client for the dedicated expediente portal.

    Requires phone number and passport/NIE match.
    """
    repository = get_repository()
    client = repository.get_client_by_id(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    from app.models.dto import validate_phone_number

    try:
        normalized_phone = validate_phone_number(request.phone_number)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    expected_phone = (client.get("phone_number") or "").strip()
    expected_passport = (client.get("passport_or_nie") or "").strip().upper()
    provided_passport = request.passport_or_nie.strip().upper()

    if normalized_phone != expected_phone or provided_passport != expected_passport:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_portal_token(client_id)
    exp = token_expiration(token)
    expires_in = max(0, (exp - int(datetime.datetime.now().timestamp()))) if exp else 3600

    return {
        "token": token,
        "expires_in": expires_in,
        "client": {
            "id": str(client_id),
            "name": client.get("name"),
            "profile_type": client.get("profile_type"),
        },
    }


@router.get("/{client_id}/portal-expediente")
async def get_portal_expediente(client_id: UUID, x_portal_token: str = Header(default="")):
    """
    Get client expediente view for dedicated portal route.

    Requires valid portal token from /portal-auth.
    """
    repository = get_repository()
    storage = get_storage()

    if not x_portal_token or not verify_portal_token(x_portal_token, client_id):
        raise HTTPException(status_code=401, detail="Invalid or expired portal token")

    client = repository.get_client_by_id(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    documents = repository.get_client_documents(client_id)
    for doc in documents:
        try:
            doc["public_url"] = storage.get_file_url(doc["storage_path"], signed=True, expires_in=3600)
        except Exception:
            doc["public_url"] = None

    checklist = _portal_checklist(documents)

    return {
        "client": {
            "id": str(client_id),
            "name": client.get("name"),
            "profile_type": client.get("profile_type"),
            "status": client.get("status"),
        },
        "checklist": checklist,
        "documents": documents,
    }


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: UUID,
    full_name: str = Form(None),
    phone_number: str = Form(None),
    passport_or_nie: str = Form(None),
    profile_type: str = Form(None),
    status_value: str = Form(None, alias="status"),
    notes: str = Form(None),
    documents: List[UploadFile] = File(default=[]),
    document_types: str = Form(default=None)  # JSON array of document types aligned with files
):
    """
    Update client information and optionally upload new documents.
    
    Args:
        client_id: Client UUID
        full_name: Client full name (optional)
        phone_number: Client phone number (optional, unique)
        passport_or_nie: Passport number or NIE (optional)
        profile_type: Profile type (ASYLUM, ARRAIGO, STUDENT, IRREGULAR, OTHER)
        status_value: Client status (active, inactive, archived)
        notes: Optional notes about the client
        documents: List of PDF files to upload
        document_types: JSON array of document types (TASA, PASSPORT_NIE), aligned with documents array
        
    Returns:
        Updated client details
        
    Raises:
        404: Client not found
        400: Invalid data or document type mismatch
        409: Phone number already exists
        500: Internal server error
    """
    repository = get_repository()
    storage = get_storage()
    
    try:
        # Verify client exists
        existing_client = repository.get_client_by_id(client_id)
        if not existing_client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        
        # Prepare update data
        update_data = {}
        
        if full_name is not None:
            update_data["name"] = full_name.strip()
        
        if passport_or_nie is not None:
            stripped_passport = passport_or_nie.strip()
            if not stripped_passport:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Passport or NIE cannot be empty"
                )
            update_data["passport_or_nie"] = stripped_passport
        
        if phone_number is not None:
            # Validate and normalize phone
            from app.models.dto import validate_phone_number
            normalized_phone = validate_phone_number(phone_number)
            
            # Check if phone is already taken by another client
            if normalized_phone != existing_client.get("phone_number"):
                # Verify uniqueness
                try:
                    update_data["phone_number"] = normalized_phone
                except ValueError as e:
                    if "already exists" in str(e):
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail=f"Phone number {phone_number} already exists"
                        )
                    raise
        
        if profile_type is not None:
            try:
                profile_enum = ProfileType(profile_type)
                update_data["profile_type"] = profile_enum.value
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid profile_type value"
                )
        
        if status_value is not None:
            try:
                status_enum = ClientStatus(status_value)
                update_data["status"] = status_enum.value
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid status value"
                )
        
        if notes is not None:
            # Update or merge with existing metadata
            metadata = existing_client.get("metadata", {}) or {}
            if notes.strip():
                metadata["notes"] = notes.strip()
            else:
                metadata.pop("notes", None)
            update_data["metadata"] = metadata
        
        # Update client if there's data to update
        if update_data:
            logger.info(f"Updating client {client_id} with data: {list(update_data.keys())}")
            updated_client = repository.update_client(client_id, update_data)
        else:
            updated_client = existing_client
        
        # Parse and validate document_types if documents provided
        parsed_doc_types = []
        if documents:
            if document_types:
                try:
                    parsed_doc_types = json.loads(document_types)
                    if len(parsed_doc_types) != len(documents):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"document_types array length ({len(parsed_doc_types)}) must match documents array length ({len(documents)})"
                        )
                    # Validate each document type
                    for dt in parsed_doc_types:
                        if dt and dt not in [DocumentType.TASA.value, DocumentType.PASSPORT_NIE.value]:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Invalid document_type '{dt}'. Must be TASA or PASSPORT_NIE"
                            )
                except json.JSONDecodeError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="document_types must be a valid JSON array"
                    )
            else:
                # If no document_types provided, fill with None (optional typing)
                parsed_doc_types = [None] * len(documents)
        
        # Upload documents if provided
        uploaded_docs = []
        if documents:
            logger.info(f"Processing {len(documents)} documents for client {client_id}")
            
            # Get current profile type for storage path
            current_profile = updated_client.get("profile_type", "OTHER")
            client_name = updated_client.get("name", "Unknown")
            
            for idx, doc in enumerate(documents):
                # Read file content
                file_content = await doc.read()
                sanitized_name = validate_pdf_upload(doc, file_content)
                doc_type = parsed_doc_types[idx]
                content_sha256 = hashlib.sha256(file_content).hexdigest()
                
                existing_doc = None
                if doc_type:
                    latest_version = repository.get_latest_document_version(client_id, doc_type)
                    if latest_version and latest_version.get("content_sha256") == content_sha256:
                        logger.info(
                            f"Skipped duplicate upload for client={client_id} doc_type={doc_type} sha256={content_sha256[:12]}"
                        )
                        continue
                    existing_doc = repository.get_document_by_client_and_type(client_id, doc_type)
                
                # Generate storage path
                timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                storage_path = f"profiles/{current_profile}/{client_name}_{client_id}/{timestamp}_{sanitized_name}"
                
                try:
                    # Upload to storage
                    storage.upload_file(storage_path, file_content, "application/pdf")
                    
                    if existing_doc:
                        merged_metadata = existing_doc.get("metadata", {}) or {}
                        merged_metadata["uploaded_via"] = "web_form_edit"
                        merged_metadata["content_sha256"] = content_sha256

                        created_doc = repository.update_document(
                            UUID(existing_doc["id"]),
                            {
                                "storage_path": storage_path,
                                "original_filename": doc.filename,
                                "mime_type": "application/pdf",
                                "file_size": len(file_content),
                                "profile_type": current_profile,
                                "metadata": merged_metadata,
                            },
                        )
                    else:
                        doc_data = {
                            "client_id": str(client_id),
                            "storage_path": storage_path,
                            "original_filename": doc.filename,
                            "mime_type": "application/pdf",
                            "file_size": len(file_content),
                            "profile_type": current_profile,
                            "document_type": doc_type if doc_type else None,
                            "metadata": {"uploaded_via": "web_form_edit", "content_sha256": content_sha256},
                        }
                        created_doc = repository.create_document(doc_data)

                    if doc_type:
                        version = _register_document_version_and_audit(
                            repository,
                            client_id=client_id,
                            document_id=created_doc["id"],
                            document_type=doc_type,
                            storage_path=storage_path,
                            original_filename=doc.filename,
                            mime_type="application/pdf",
                            file_size=len(file_content),
                            content_sha256=content_sha256,
                            actor="staff",
                        )
                        if version:
                            metadata = created_doc.get("metadata", {}) or {}
                            metadata["current_version_id"] = version["id"]
                            metadata["current_version_number"] = version["version_number"]
                            created_doc = repository.update_document(UUID(created_doc["id"]), {"metadata": metadata})

                    uploaded_docs.append(created_doc)
                    logger.info(f"Document uploaded: {doc.filename} ({doc_type or 'untyped'}) -> {storage_path}")
                    
                except Exception as e:
                    logger.error(f"Error uploading document {doc.filename}: {e}")
                    # Continue with other documents
        
        # Update document count in metadata
        if uploaded_docs:
            current_metadata = updated_client.get("metadata", {}) or {}
            # Recalculate total document count from database
            all_docs = repository.get_client_documents(client_id)
            current_metadata["document_count"] = len(all_docs)
            repository.update_client(client_id, {"metadata": current_metadata})
            updated_client["metadata"] = current_metadata
        
        return ClientResponse(**updated_client)
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error updating client: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating client {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update client: {str(e)}"
        )


@router.post("/{client_id}/documents", status_code=status.HTTP_201_CREATED)
async def upload_client_documents(
    client_id: UUID,
    documents: List[UploadFile] = File(...),
    document_types: str = Form(default=None)  # JSON array of document types aligned with files
):
    """
    Upload additional documents for an existing client.
    
    Args:
        client_id: Client UUID
        documents: List of PDF files to upload
        document_types: JSON array of document types (TASA, PASSPORT_NIE), aligned with documents array
        
    Returns:
        Summary of uploaded documents
        
    Raises:
        404: Client not found
        400: Invalid file type or document type mismatch
        500: Internal server error
    """
    repository = get_repository()
    storage = get_storage()
    
    try:
        # Verify client exists
        client = repository.get_client_by_id(client_id)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        
        if not documents:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No documents provided"
            )
        
        # Parse and validate document_types
        parsed_doc_types = []
        if document_types:
            try:
                parsed_doc_types = json.loads(document_types)
                if len(parsed_doc_types) != len(documents):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"document_types array length ({len(parsed_doc_types)}) must match documents array length ({len(documents)})"
                    )
                # Validate each document type
                for dt in parsed_doc_types:
                    if dt and dt not in [DocumentType.TASA.value, DocumentType.PASSPORT_NIE.value]:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid document_type '{dt}'. Must be TASA or PASSPORT_NIE"
                        )
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="document_types must be a valid JSON array"
                )
        else:
            # If no document_types provided, fill with None
            parsed_doc_types = [None] * len(documents)
        
        logger.info(f"Uploading {len(documents)} documents for client {client_id}")
        
        uploaded_docs = []
        errors = []
        
        current_profile = client.get("profile_type", "OTHER")
        client_name = client.get("name", "Unknown")
        
        for idx, doc in enumerate(documents):
            # Read file content
            file_content = await doc.read()
            try:
                sanitized_name = validate_pdf_upload(doc, file_content)
            except HTTPException as e:
                errors.append(e.detail)
                continue
            doc_type = parsed_doc_types[idx]
            content_sha256 = hashlib.sha256(file_content).hexdigest()
            
            existing_doc = None
            if doc_type:
                latest_version = repository.get_latest_document_version(client_id, doc_type)
                if latest_version and latest_version.get("content_sha256") == content_sha256:
                    errors.append(f"{sanitized_name}: Duplicate content for {doc_type} (same SHA256)")
                    continue
                existing_doc = repository.get_document_by_client_and_type(client_id, doc_type)
            
            # Generate storage path
            timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            storage_path = f"profiles/{current_profile}/{client_name}_{client_id}/{timestamp}_{sanitized_name}"
            
            try:
                # Upload to storage
                storage.upload_file(storage_path, file_content, "application/pdf")
                
                if existing_doc:
                    merged_metadata = existing_doc.get("metadata", {}) or {}
                    merged_metadata["uploaded_via"] = "web_form_upload"
                    merged_metadata["content_sha256"] = content_sha256
                    created_doc = repository.update_document(
                        UUID(existing_doc["id"]),
                        {
                            "storage_path": storage_path,
                            "original_filename": doc.filename,
                            "mime_type": "application/pdf",
                            "file_size": len(file_content),
                            "profile_type": current_profile,
                            "metadata": merged_metadata,
                        },
                    )
                else:
                    doc_data = {
                        "client_id": str(client_id),
                        "storage_path": storage_path,
                        "original_filename": doc.filename,
                        "mime_type": "application/pdf",
                        "file_size": len(file_content),
                        "profile_type": current_profile,
                        "document_type": doc_type if doc_type else None,
                        "metadata": {"uploaded_via": "web_form_upload", "content_sha256": content_sha256},
                    }
                    created_doc = repository.create_document(doc_data)

                if doc_type:
                    version = _register_document_version_and_audit(
                        repository,
                        client_id=client_id,
                        document_id=created_doc["id"],
                        document_type=doc_type,
                        storage_path=storage_path,
                        original_filename=doc.filename,
                        mime_type="application/pdf",
                        file_size=len(file_content),
                        content_sha256=content_sha256,
                        actor="staff",
                    )
                    if version:
                        metadata = created_doc.get("metadata", {}) or {}
                        metadata["current_version_id"] = version["id"]
                        metadata["current_version_number"] = version["version_number"]
                        created_doc = repository.update_document(UUID(created_doc["id"]), {"metadata": metadata})

                uploaded_docs.append(
                    {
                        "filename": doc.filename,
                        "size": len(file_content),
                        "document_type": doc_type,
                        "document_id": created_doc["id"],
                    }
                )
                
                logger.info(f"Document uploaded: {doc.filename} ({doc_type or 'untyped'}) -> {storage_path}")
                
            except Exception as e:
                logger.error(f"Error uploading document {doc.filename}: {e}")
                errors.append(f"{doc.filename}: {str(e)}")
        
        # Update document count in metadata
        if uploaded_docs:
            metadata = client.get("metadata", {}) or {}
            # Recalculate total document count from database
            all_docs = repository.get_client_documents(client_id)
            metadata["document_count"] = len(all_docs)
            repository.update_client(client_id, {"metadata": metadata})
        
        return {
            "uploaded": len(uploaded_docs),
            "failed": len(errors),
            "documents": uploaded_docs,
            "errors": errors if errors else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading documents for client {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload documents: {str(e)}"
        )


@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    full_name: str = Form(...),
    phone_number: str = Form(...),
    passport_or_nie: str = Form(...),
    email: str = Form(default=None),
    profile_type: str = Form(default="OTHER"),
    status_value: str = Form(default="active", alias="status"),
    notes: str = Form(default=None),
    documents: List[UploadFile] = File(default=[]),
    document_types: str = Form(default=None)  # JSON array of document types aligned with files
):
    """
    Create a new client with optional PDF documents.
    
    Args:
        full_name: Client full name (required)
        phone_number: Client phone number (required, unique)
        passport_or_nie: Passport number or NIE (required)
        email: Client email address (optional)
        profile_type: Profile type (ASYLUM, ARRAIGO, STUDENT, IRREGULAR, OTHER)
        status_value: Client status (active, inactive, archived)
        notes: Optional notes about the client
        documents: List of PDF files to upload
        document_types: JSON array of document types (TASA, PASSPORT_NIE), aligned with documents array
        
    Returns:
        Created client details with uploaded documents
        
    Raises:
        400: Invalid phone number format, file type, or document type mismatch
        409: Phone number already exists
        500: Internal server error
    """
    repository = get_repository()
    storage = get_storage()
    
    try:
        # Validate passport_or_nie
        stripped_passport = passport_or_nie.strip()
        if not stripped_passport:
            raise ValueError("Passport or NIE cannot be empty")
        
        # Validate and normalize phone
        from app.models.dto import validate_phone_number
        normalized_phone = validate_phone_number(phone_number)
        
        # Validate profile type and status
        try:
            profile_enum = ProfileType(profile_type)
            status_enum = ClientStatus(status_value)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid profile_type or status value"
            )
        
        # Parse and validate document_types if documents provided
        parsed_doc_types = []
        if documents:
            logger.info(f"Received {len(documents)} documents")
            logger.info(f"document_types parameter: {repr(document_types)}")
            
            if document_types:
                try:
                    parsed_doc_types = json.loads(document_types)
                    logger.info(f"Parsed document_types: {parsed_doc_types}")
                    
                    if len(parsed_doc_types) != len(documents):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"document_types array length ({len(parsed_doc_types)}) must match documents array length ({len(documents)})"
                        )
                    # Validate each document type
                    for dt in parsed_doc_types:
                        if dt and dt not in [DocumentType.TASA.value, DocumentType.PASSPORT_NIE.value]:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Invalid document_type '{dt}'. Must be TASA or PASSPORT_NIE"
                            )
                except json.JSONDecodeError as je:
                    logger.error(f"JSON decode error: {je}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="document_types must be a valid JSON array"
                    )
            else:
                logger.warning("No document_types provided, all documents will be untyped")
                # If no document_types provided, fill with None
                parsed_doc_types = [None] * len(documents)
        
        # Prepare client data
        client_data = {
            "name": full_name.strip(),
            "phone_number": normalized_phone,
            "passport_or_nie": stripped_passport,
            "email": email.strip() if email else None,
            "notes": notes.strip() if notes else None,
            "profile_type": profile_enum.value,
            "status": status_enum.value,
            "metadata": {}
        }
        
        logger.info(f"Creating client with phone: {normalized_phone}")
        
        # Create client in database
        created_client = repository.create_client(client_data)
        client_id = created_client['id']
        
        logger.info(f"Client created successfully: {client_id}")
        
        # Upload documents if provided
        uploaded_docs = []
        if documents:
            logger.info(f"Processing {len(documents)} documents for client {client_id}")
            
            for idx, doc in enumerate(documents):
                # Read file content
                file_content = await doc.read()
                sanitized_name = validate_pdf_upload(doc, file_content)
                doc_type = parsed_doc_types[idx]
                content_sha256 = hashlib.sha256(file_content).hexdigest()
                
                # Generate storage path
                timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                storage_path = f"profiles/{profile_enum.value}/{full_name}_{client_id}/{timestamp}_{sanitized_name}"
                
                try:
                    # Upload to storage
                    storage.upload_file(storage_path, file_content, "application/pdf")
                    
                    doc_data = {
                        "client_id": client_id,
                        "storage_path": storage_path,
                        "original_filename": doc.filename,
                        "mime_type": "application/pdf",
                        "file_size": len(file_content),
                        "profile_type": profile_enum.value,
                        "document_type": doc_type if doc_type else None,
                        "metadata": {"uploaded_via": "web_form", "content_sha256": content_sha256},
                    }
                    created_doc = repository.create_document(doc_data)

                    if doc_type:
                        version = _register_document_version_and_audit(
                            repository,
                            client_id=UUID(client_id),
                            document_id=created_doc["id"],
                            document_type=doc_type,
                            storage_path=storage_path,
                            original_filename=doc.filename,
                            mime_type="application/pdf",
                            file_size=len(file_content),
                            content_sha256=content_sha256,
                            actor="staff",
                        )
                        if version:
                            metadata = created_doc.get("metadata", {}) or {}
                            metadata["current_version_id"] = version["id"]
                            metadata["current_version_number"] = version["version_number"]
                            created_doc = repository.update_document(UUID(created_doc["id"]), {"metadata": metadata})

                    uploaded_docs.append(created_doc)
                    
                    logger.info(f"Document uploaded: {doc.filename} ({doc_type or 'untyped'}) -> {storage_path}")
                    
                except Exception as e:
                    logger.error(f"Error uploading document {doc.filename}: {e}")
                    # Continue with other documents, don't fail entire request
        
        # Add document count to metadata
        if uploaded_docs:
            created_client['metadata']['document_count'] = len(uploaded_docs)
        
        return ClientResponse(**created_client)
        
    except ValueError as e:
        # Handle duplicate phone number or validation errors
        error_msg = str(e)
        if "already exists" in error_msg:
            logger.warning(f"Duplicate phone number attempt: {phone_number}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Phone number {phone_number} already exists"
            )
        # Handle validation errors
        logger.error(f"Validation error creating client: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating client: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create client: {str(e)}"
        )


@router.post("/{client_id}/expediente")
async def generate_expediente(client_id: UUID):
    """
    Generate expediente ZIP file for a client with required documents.
    
    The ZIP contains:
    - Folder: {client_name}_{client_id_short}/
    - Files: Tasa_{name}.pdf and {NIE|Pasaporte}_{name}.pdf
    
    Args:
        client_id: Client UUID
        
    Returns:
        ZIP file download with proper filename
        
    Raises:
        404: Client not found
        400: Missing required documents or passport_or_nie field
        500: Internal server error
    """
    try:
        # Generate ZIP
        zip_bytes, folder_name = generate_expediente_zip(client_id)
        
        # Return as streaming response with download headers
        # Ensure filename matches folder name inside ZIP
        zip_filename = f"{folder_name}.zip"
        return StreamingResponse(
            iter([zip_bytes]),
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{zip_filename}"',
                "Content-Length": str(len(zip_bytes))
            }
        )
        
    except ValueError as e:
        # Client not found
        logger.error(f"Client not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except MissingDocumentsError as e:
        # Missing required documents
        logger.warning(f"Missing documents for expediente: {e.missing}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Missing required documents",
                "missing": e.missing,
                "message": "Cannot generate expediente. Please upload all required documents (TASA and PASSPORT_NIE)."
            }
        )
    except Exception as e:
        logger.error(f"Error generating expediente for client {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate expediente: {str(e)}"
        )


@router.post("/{client_id}/exports")
async def create_export_job(
    client_id: UUID,
    request: ExportJobRequest,
    x_portal_token: str = Header(default=""),
):
    """
    Generate expediente ZIP and register an export job with expiring signed URL.

    By default exports only documents already accepted in review.
    """
    repository = get_repository()
    storage = get_storage()

    if request.expires_in < 300 or request.expires_in > 86400:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="expires_in must be between 300 and 86400 seconds",
        )

    requester = (request.requested_by or "staff").strip().lower()
    if requester == "client":
        if not x_portal_token or not verify_portal_token(x_portal_token, client_id):
            raise HTTPException(status_code=401, detail="Invalid or expired portal token")

    try:
        zip_bytes, folder_name = generate_expediente_zip(client_id, accepted_only=request.accepted_only)
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        export_filename = f"{timestamp}_{folder_name}.zip"
        export_storage_path = f"{client_id}/{export_filename}"

        # Prefer dedicated exports bucket in real mode.
        signed_url = None
        from app.core.config import get_settings
        settings = get_settings()
        if settings.app_mode == "real":
            from app.db.supabase import get_supabase_client
            supabase_client = get_supabase_client()
            supabase_client.client.storage.from_("exports").upload(
                export_storage_path,
                zip_bytes,
                file_options={"content-type": "application/zip"},
            )
            signed_resp = supabase_client.client.storage.from_("exports").create_signed_url(
                export_storage_path,
                request.expires_in,
            )
            signed_url = signed_resp.get("signedURL")
        else:
            # Mock fallback (stores under local mock storage tree)
            mock_path = f"exports/{export_storage_path}"
            storage.upload_file(mock_path, zip_bytes, "application/zip")
            signed_url = storage.get_file_url(mock_path, signed=True, expires_in=request.expires_in)
            export_storage_path = mock_path

        expires_at = (
            datetime.datetime.utcnow() + datetime.timedelta(seconds=request.expires_in)
        ).replace(microsecond=0).isoformat() + "Z"

        export_job = repository.create_export_job(
            {
                "client_id": str(client_id),
                "storage_path": export_storage_path,
                "status": "ready",
                "accepted_only": request.accepted_only,
                "file_size": len(zip_bytes),
                "expires_at": expires_at,
                "requested_by": requester,
                "metadata": {
                    "filename": export_filename,
                    "bucket": "exports" if settings.app_mode == "real" else "mock-storage",
                },
            }
        )

        try:
            repository.create_audit_event(
                {
                    "client_id": str(client_id),
                    "event_type": "EXPORT_READY",
                    "actor": requester,
                    "details": {
                        "export_job_id": export_job["id"],
                        "storage_path": export_storage_path,
                        "accepted_only": request.accepted_only,
                        "expires_at": expires_at,
                    },
                }
            )
        except Exception as audit_error:
            logger.warning(f"Failed to persist export audit event for client {client_id}: {audit_error}")

        return {
            "export_job_id": export_job["id"],
            "client_id": str(client_id),
            "status": export_job.get("status", "ready"),
            "accepted_only": request.accepted_only,
            "storage_path": export_storage_path,
            "filename": export_filename,
            "signed_url": signed_url,
            "expires_in": request.expires_in,
            "expires_at": expires_at,
        }

    except ValueError as e:
        logger.error(f"Export client not found: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except MissingDocumentsError as e:
        logger.warning(f"Missing documents for export client {client_id}: {e.missing}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Missing required documents",
                "missing": e.missing,
                "accepted_only": request.accepted_only,
                "message": "Cannot export expediente. Required documents are missing for current constraints.",
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating export job for client {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create export job: {str(e)}",
        )
