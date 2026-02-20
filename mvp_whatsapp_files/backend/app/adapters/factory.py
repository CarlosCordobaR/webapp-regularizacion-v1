"""Adapter factory for dependency injection."""

from app.adapters.repository_base import RepositoryBase
from app.adapters.storage_base import StorageBase
from app.adapters.whatsapp_base import WhatsAppBase
from app.adapters.mock.mock_repository import MockRepository
from app.adapters.mock.mock_storage import MockStorage
from app.adapters.mock.mock_whatsapp import MockWhatsAppClient
from app.adapters.real.supabase_repository import SupabaseRepository
from app.adapters.real.supabase_storage import SupabaseStorage
from app.adapters.real.meta_whatsapp import MetaWhatsAppClient
from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.supabase import get_supabase_client
from app.whatsapp.client import WhatsAppClient

logger = get_logger(__name__)

# Global instances
_repository_instance = None
_storage_instance = None
_whatsapp_instance = None


def get_repository() -> RepositoryBase:
    """Get repository instance based on configuration."""
    global _repository_instance
    
    if _repository_instance is None:
        settings = get_settings()
        
        if settings.app_mode == "mock":
            logger.info("Initializing MockRepository")
            _repository_instance = MockRepository()
        else:
            logger.info("Initializing SupabaseRepository")
            supabase_client = get_supabase_client()
            _repository_instance = SupabaseRepository(supabase_client)
    
    return _repository_instance


def get_storage() -> StorageBase:
    """Get storage instance based on configuration."""
    global _storage_instance
    
    if _storage_instance is None:
        settings = get_settings()
        
        if settings.storage_mode == "local":
            logger.info("Initializing MockStorage")
            _storage_instance = MockStorage()
        else:
            logger.info("Initializing SupabaseStorage")
            supabase_client = get_supabase_client()
            _storage_instance = SupabaseStorage(supabase_client)
    
    return _storage_instance


def get_whatsapp_client() -> WhatsAppBase:
    """Get WhatsApp client instance based on configuration."""
    global _whatsapp_instance
    
    if _whatsapp_instance is None:
        settings = get_settings()
        
        if settings.app_mode == "mock":
            logger.info("Initializing MockWhatsAppClient")
            _whatsapp_instance = MockWhatsAppClient()
        else:
            logger.info("Initializing MetaWhatsAppClient")
            real_client = WhatsAppClient()
            _whatsapp_instance = MetaWhatsAppClient(real_client)
    
    return _whatsapp_instance


def reset_instances():
    """Reset all adapter instances (useful for testing)."""
    global _repository_instance, _storage_instance, _whatsapp_instance
    _repository_instance = None
    _storage_instance = None
    _whatsapp_instance = None
