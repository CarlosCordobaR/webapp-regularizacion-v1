"""Mock dataset seed generator."""
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict
from uuid import uuid4

from app.adapters.mock.mock_repository import MockRepository
from app.adapters.mock.mock_storage import MockStorage
from app.core.logging import get_logger

logger = get_logger(__name__)


# Mock client data
MOCK_CLIENTS = [
    {
        "name": "María González",
        "phone": "+34612345001",
        "profile": "ASYLUM",
        "keywords": ["asilo", "refugio", "persecución"],
        "docs": ["pasaporte.pdf", "carta_asilo.pdf", "prueba_identidad.pdf"]
    },
    {
        "name": "Carlos Rodríguez",
        "phone": "+34612345002",
        "profile": "ARRAIGO",
        "keywords": ["arraigo", "familiar", "empadronamiento"],
        "docs": ["empadronamiento.pdf", "contrato_trabajo.pdf"]
    },
    {
        "name": "Ana Martínez",
        "phone": "+34612345003",
        "profile": "STUDENT",
        "keywords": ["estudiante", "universidad", "matrícula"],
        "docs": ["certificado_matricula.pdf", "carta_admision.pdf"]
    },
    {
        "name": "Luis Hernández",
        "phone": "+34612345004",
        "profile": "IRREGULAR",
        "keywords": ["irregular", "documentación", "situación"],
        "docs": ["pasaporte.pdf", "solicitud_regularizacion.pdf"]
    },
    {
        "name": "Elena Pérez",
        "phone": "+34612345005",
        "profile": "ASYLUM",
        "keywords": ["asilo", "político", "protección"],
        "docs": ["pasaporte.pdf", "informe_situacion.pdf", "carta_apoyo.pdf"]
    },
    {
        "name": "Jorge Sánchez",
        "phone": "+34612345006",
        "profile": "OTHER",
        "keywords": ["información", "consulta", "trámites"],
        "docs": ["pasaporte.pdf"]
    },
    {
        "name": "Carmen López",
        "phone": "+34612345007",
        "profile": "ARRAIGO",
        "keywords": ["arraigo", "social", "laboral"],
        "docs": ["empadronamiento.pdf", "nomina.pdf", "contrato_alquiler.pdf"]
    },
    {
        "name": "Miguel Torres",
        "phone": "+34612345008",
        "profile": "STUDENT",
        "keywords": ["estudiante", "máster", "beca"],
        "docs": ["certificado_matricula.pdf", "carta_beca.pdf"]
    },
    {
        "name": "Isabel Ramírez",
        "phone": "+34612345009",
        "profile": "IRREGULAR",
        "keywords": ["irregular", "vencida", "renovación"],
        "docs": ["pasaporte.pdf", "nie_caducado.pdf"]
    },
    {
        "name": "David Flores",
        "phone": "+34612345010",
        "profile": "OTHER",
        "keywords": ["general", "dudas", "procedimiento"],
        "docs": ["dni.pdf"]
    }
]

# Message templates
INBOUND_TEMPLATES = [
    "Hola, necesito ayuda con mi {keyword}",
    "Buenos días, quisiera información sobre {keyword}",
    "Me podrían orientar con el proceso de {keyword}?",
    "Tengo una consulta sobre {keyword}",
    "Necesito asesoramiento en {keyword}",
    "¿Qué documentos necesito para {keyword}?",
    "Mi situación es de {keyword}",
    "Estoy en proceso de {keyword}",
    "¿Cuánto tiempo tarda el trámite de {keyword}?",
    "Adjunto los documentos requeridos",
    "¿Recibieron mi solicitud?",
    "¿Hay alguna actualización?",
]

OUTBOUND_TEMPLATES = [
    "Gracias por contactarnos. ¿En qué podemos ayudarte?",
    "Hemos recibido tu consulta. Te responderemos pronto.",
    "Por favor, envía los documentos solicitados.",
    "Tu solicitud está en revisión.",
    "Necesitamos documentación adicional.",
    "El proceso puede tardar entre 2-4 semanas.",
]


def generate_dummy_pdf(filename: str) -> bytes:
    """Generate a minimal valid PDF file."""
    # Minimal PDF structure
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(""" + filename.encode('latin-1') + b""") Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000317 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
410
%%EOF
"""
    return pdf_content


def create_fixture_pdfs(fixtures_path: Path):
    """Create fixture PDF files."""
    fixtures_path.mkdir(parents=True, exist_ok=True)
    
    document_types = [
        "pasaporte.pdf",
        "empadronamiento.pdf",
        "certificado_matricula.pdf",
        "carta_asilo.pdf",
        "prueba_identidad.pdf",
        "contrato_trabajo.pdf",
        "carta_admision.pdf",
        "solicitud_regularizacion.pdf",
        "informe_situacion.pdf",
        "carta_apoyo.pdf",
        "nomina.pdf",
        "contrato_alquiler.pdf",
        "carta_beca.pdf",
        "nie_caducado.pdf",
        "dni.pdf",
    ]
    
    for doc_type in document_types:
        file_path = fixtures_path / doc_type
        if not file_path.exists():
            pdf_content = generate_dummy_pdf(doc_type)
            with open(file_path, 'wb') as f:
                f.write(pdf_content)
            logger.info(f"Created fixture PDF: {doc_type}")


def seed_mock_data(repository: MockRepository, storage: MockStorage):
    """Seed mock database with test data."""
    fixtures_path = Path("backend/app/fixtures/pdfs")
    
    # Create fixture PDFs
    create_fixture_pdfs(fixtures_path)
    
    # Check if already seeded
    clients, total = repository.get_clients(page=1, page_size=1)
    if total > 0:
        logger.info(f"Database already seeded with {total} clients. Skipping.")
        return
    
    logger.info("Starting mock data seeding...")
    
    conversation_count = 0
    document_count = 0
    
    for client_data in MOCK_CLIENTS:
        # Create client
        client_id = str(uuid4())
        client = {
            "id": client_id,
            "phone_number": client_data["phone"],
            "name": client_data["name"],
            "profile_type": client_data["profile"],
            "status": "active",
            "metadata": {}
        }
        
        # Insert into DB manually to control ID
        cursor = repository.conn.cursor()
        cursor.execute("""
            INSERT INTO clients (id, phone_number, name, profile_type, status, metadata)
            VALUES (?, ?, ?, ?, ?, '{}')
        """, (client_id, client["phone_number"], client["name"], 
              client["profile_type"], client["status"]))
        repository.conn.commit()
        
        # Generate conversations
        base_time = datetime.now() - timedelta(days=random.randint(7, 30))
        num_inbound = random.randint(6, 12)
        num_outbound = random.randint(2, 4)
        
        # Inbound messages
        for i in range(num_inbound):
            keyword = random.choice(client_data["keywords"])
            template = random.choice(INBOUND_TEMPLATES)
            content = template.format(keyword=keyword)
            
            conversation_id = str(uuid4())
            message_time = base_time + timedelta(hours=i * 3, minutes=random.randint(0, 180))
            
            cursor.execute("""
                INSERT INTO conversations (id, client_id, message_id, direction, content, 
                                         message_type, metadata, created_at)
                VALUES (?, ?, ?, 'inbound', ?, 'text', '{}', ?)
            """, (conversation_id, client_id, f"wamid_{client_id}_{i}", 
                  content, message_time.isoformat()))
            conversation_count += 1
        
        # Outbound messages
        for i in range(num_outbound):
            content = random.choice(OUTBOUND_TEMPLATES)
            conversation_id = str(uuid4())
            message_time = base_time + timedelta(hours=(i + 1) * 8, minutes=random.randint(0, 180))
            
            cursor.execute("""
                INSERT INTO conversations (id, client_id, message_id, direction, content, 
                                         message_type, metadata, created_at)
                VALUES (?, ?, ?, 'outbound', ?, 'text', '{}', ?)
            """, (conversation_id, client_id, f"wamid_out_{client_id}_{i}", 
                  content, message_time.isoformat()))
            conversation_count += 1
        
        repository.conn.commit()
        
        # Store documents
        for doc_filename in client_data["docs"]:
            fixture_path = fixtures_path / doc_filename
            if not fixture_path.exists():
                continue
            
            # Read fixture PDF
            with open(fixture_path, 'rb') as f:
                file_data = f.read()
            
            # Generate storage path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            storage_path = f"profiles/{client_data['profile']}/{client_data['name'].replace(' ', '_')}_{client_id}/{timestamp}_{doc_filename}"
            
            # Upload to mock storage
            storage.upload_file(storage_path, file_data, "application/pdf")
            
            # Create document record
            document_id = str(uuid4())
            upload_time = base_time + timedelta(days=random.randint(1, 5))
            
            cursor.execute("""
                INSERT INTO documents (id, client_id, conversation_id, storage_path, 
                                     original_filename, mime_type, file_size, profile_type,
                                     metadata, uploaded_at)
                VALUES (?, ?, NULL, ?, ?, 'application/pdf', ?, ?, '{}', ?)
            """, (document_id, client_id, storage_path, doc_filename, 
                  len(file_data), client_data['profile'], upload_time.isoformat()))
            document_count += 1
        
        repository.conn.commit()
    
    logger.info(f"Seeding complete! Created {len(MOCK_CLIENTS)} clients, "
                f"{conversation_count} conversations, {document_count} documents")


def get_seed_summary(repository: MockRepository) -> Dict[str, int]:
    """Get summary of seeded data."""
    cursor = repository.conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM clients")
    clients = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM conversations")
    conversations = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM documents")
    documents = cursor.fetchone()[0]
    
    return {
        "clients": clients,
        "conversations": conversations,
        "documents": documents
    }
