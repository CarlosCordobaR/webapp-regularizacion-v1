import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api, Client, Conversation, Document } from '../lib/api'
import AppHeader from '../components/AppHeader'
import ConversationList from '../components/ConversationList.tsx'
import DocumentList from '../components/DocumentList.tsx'
import EditClientModal from '../components/EditClientModal.tsx'

type ChecklistStatus = 'missing' | 'uploaded' | 'accepted' | 'rejected'

export default function ClientDetail() {
  const { id } = useParams<{ id: string }>()
  const [client, setClient] = useState<Client | null>(null)
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    if (id) {
      loadClientData()
    }
  }, [id])

  const loadClientData = async () => {
    if (!id) return

    try {
      setLoading(true)
      const [clientData, conversationsData, documentsData] = await Promise.all([
        api.getClient(id),
        api.getClientConversations(id),
        api.getClientDocuments(id),
      ])

      setClient(clientData)
      setConversations(conversationsData.data)
      setDocuments(documentsData.data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load client data')
    } finally {
      setLoading(false)
    }
  }

  const handleClientUpdated = () => {
    // Reload client data after successful update
    loadClientData()
  }

  if (loading) {
    return (
      <>
        <AppHeader />
        <div className="loading-container">
          <div className="spinner"></div>
        </div>
      </>
    )
  }

  if (error) {
    return (
      <>
        <AppHeader />
        <div className="page-container">
          <div className="alert alert-error">Error: {error}</div>
        </div>
      </>
    )
  }

  if (!client) {
    return (
      <>
        <AppHeader />
        <div className="page-container">
          <div className="alert alert-warning">Client not found</div>
        </div>
      </>
    )
  }

  return (
    <>
      <AppHeader />
      <div className="page-container">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <button onClick={() => navigate('/clients', { replace: false })} className="btn btn-secondary">
            ← Volver a Clientes
          </button>
          <button 
            onClick={() => setIsEditModalOpen(true)} 
            className="btn btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
          >
            ✏️ Editar Cliente
          </button>
        </div>

        <div className="card" style={{ marginBottom: '30px' }}>
          <h1 style={{ marginBottom: '20px', fontSize: '1.75rem' }}>{client.name || 'Unknown'}</h1>
          <div style={{ display: 'grid', gridTemplateColumns: '150px 1fr', gap: '12px' }}>
            <strong style={{ color: 'var(--text-secondary)' }}>Phone:</strong>
            <span>{client.phone_number}</span>
            
            <strong style={{ color: 'var(--text-secondary)' }}>Email:</strong>
            <span style={{ color: client.email ? 'var(--text-primary)' : 'var(--text-secondary)', fontStyle: client.email ? 'normal' : 'italic' }}>
              {client.email || 'No email provided'}
            </span>
            
            <strong style={{ color: 'var(--text-secondary)' }}>Passport/NIE:</strong>
            <span>{client.passport_or_nie || '—'}</span>
            
            <strong style={{ color: 'var(--text-secondary)' }}>Profile Type:</strong>
            <span className={`badge badge-${getProfileBadgeType(client.profile_type)}`}>
              {client.profile_type}
            </span>
            
            <strong style={{ color: 'var(--text-secondary)' }}>Status:</strong>
            <span className={`badge badge-${getStatusBadgeType(client.status)}`}>
              {client.status}
            </span>
            
            <strong style={{ color: 'var(--text-secondary)' }}>Created:</strong>
            <span>{new Date(client.created_at).toLocaleString()}</span>
            
            {(client.notes || client.metadata?.notes) && (
              <>
                <strong style={{ color: 'var(--text-secondary)' }}>Notes:</strong>
                <span style={{ whiteSpace: 'pre-wrap' }}>{client.notes || client.metadata?.notes}</span>
              </>
            )}
            
            {client.metadata?.document_count !== undefined && (
              <>
                <strong style={{ color: 'var(--text-secondary)' }}>Documents:</strong>
                <span>{client.metadata.document_count} uploaded</span>
              </>
            )}
          </div>
        </div>

        <div style={{ marginBottom: '30px' }}>
          <h2 style={{ marginBottom: '15px', fontSize: '1.5rem' }}>
            💬 Conversaciones ({conversations.length})
          </h2>
          <ConversationList conversations={conversations} />
        </div>

        <div>
          <h2 style={{ marginBottom: '15px', fontSize: '1.5rem' }}>
            📄 Documentos ({documents.length})
          </h2>
          <div className="card" style={{ marginBottom: '15px' }}>
            <h3 style={{ marginBottom: '12px', fontSize: '1.1rem' }}>🧾 Mi Expediente</h3>
            <div style={{ display: 'grid', gap: '10px' }}>
              {buildChecklistRows(documents).map((row) => (
                <div
                  key={row.type}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    gap: '10px',
                    padding: '10px 12px',
                    border: '1px solid var(--border)',
                    borderRadius: '8px',
                    backgroundColor: 'var(--bg-secondary)',
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 600 }}>{row.label}</div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{row.message}</div>
                  </div>
                  <span className={`badge badge-${checklistBadge(row.status)}`}>{checklistLabel(row.status)}</span>
                </div>
              ))}
            </div>
          </div>
          <DocumentList documents={documents} onReviewed={loadClientData} />
        </div>
      </div>

      <EditClientModal
        isOpen={isEditModalOpen}
        client={client}
        onClose={() => setIsEditModalOpen(false)}
        onSuccess={handleClientUpdated}
      />
    </>
  )
}

function getProfileBadgeType(profileType: string): string {
  const types: Record<string, string> = {
    ASYLUM: 'error',
    ARRAIGO: 'info',
    STUDENT: 'success',
    IRREGULAR: 'warning',
    OTHER: 'info',
  }
  return types[profileType] || 'info'
}

function getStatusBadgeType(status: string): string {
  const types: Record<string, string> = {
    active: 'success',
    inactive: 'warning',
    archived: 'info',
  }
  return types[status] || 'info'
}

function checklistLabel(status: ChecklistStatus): string {
  const labels: Record<ChecklistStatus, string> = {
    missing: 'Missing',
    uploaded: 'Uploaded',
    accepted: 'Accepted',
    rejected: 'Rejected',
  }
  return labels[status]
}

function checklistBadge(status: ChecklistStatus): string {
  const badges: Record<ChecklistStatus, string> = {
    missing: 'warning',
    uploaded: 'info',
    accepted: 'success',
    rejected: 'error',
  }
  return badges[status]
}

function buildChecklistRows(documents: Document[]) {
  const required = [
    { type: 'TASA', label: 'Comprobante TASA' },
    { type: 'PASSPORT_NIE', label: 'Pasaporte / NIE' },
  ]

  return required.map((item) => {
    const typedDocs = documents
      .filter((doc) => doc.document_type === item.type)
      .sort((a, b) => new Date(b.uploaded_at).getTime() - new Date(a.uploaded_at).getTime())

    const current = typedDocs[0]
    if (!current) {
      return {
        type: item.type,
        label: item.label,
        status: 'missing' as ChecklistStatus,
        message: 'Pendiente de carga.',
      }
    }

    const review = current.metadata?.review_status
    if (review === 'accepted') {
      return {
        type: item.type,
        label: item.label,
        status: 'accepted' as ChecklistStatus,
        message: 'Documento validado por el equipo.',
      }
    }

    if (review === 'rejected') {
      const note = current.metadata?.review_note
      return {
        type: item.type,
        label: item.label,
        status: 'rejected' as ChecklistStatus,
        message: note ? `Rechazado: ${note}` : 'Rechazado por revisión.',
      }
    }

    return {
      type: item.type,
      label: item.label,
      status: 'uploaded' as ChecklistStatus,
      message: 'Cargado y pendiente de revisión.',
    }
  })
}
