import { useState } from 'react'
import { api, Document } from '../lib/api'

interface DocumentListProps {
  documents: Document[]
  onReviewed?: () => void
}

export default function DocumentList({ documents, onReviewed }: DocumentListProps) {
  const [reviewingId, setReviewingId] = useState<string | null>(null)

  if (documents.length === 0) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '3rem', backgroundColor: 'var(--bg-secondary)' }}>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', marginBottom: '0.5rem' }}>
          📄 No hay documentos cargados
        </p>
        <p style={{ color: 'var(--text-tertiary)', fontSize: '0.875rem' }}>
          Los documentos subidos al crear el cliente aparecerán aquí
        </p>
      </div>
    )
  }

  const formatFileSize = (bytes: number | null): string => {
    if (!bytes) return 'Unknown'
    const kb = bytes / 1024
    if (kb < 1024) return `${kb.toFixed(1)} KB`
    return `${(kb / 1024).toFixed(1)} MB`
  }

  const reviewLabel = (doc: Document): string => {
    const status = doc.metadata?.review_status
    if (status === 'accepted') return 'Aceptado'
    if (status === 'rejected') return 'Rechazado'
    return 'Pendiente'
  }

  const handleReview = async (doc: Document, action: 'accepted' | 'rejected') => {
    try {
      setReviewingId(doc.id)
      let note: string | undefined
      if (action === 'rejected') {
        const input = window.prompt('Motivo del rechazo (obligatorio):', '')
        if (!input || !input.trim()) {
          alert('Debes indicar una nota para rechazar.')
          return
        }
        note = input.trim()
      }

      await api.reviewDocument(doc.id, action, note)
      onReviewed?.()
    } catch (error) {
      const message = error instanceof Error ? error.message : 'No se pudo revisar el documento'
      alert(message)
    } finally {
      setReviewingId(null)
    }
  }

  return (
    <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
      <div className="table-container" style={{ margin: 0 }}>
        <table>
          <thead>
            <tr>
              <th style={{ paddingLeft: '1.5rem' }}>📄 Archivo</th>
              <th>Tipo</th>
              <th>Tamaño</th>
              <th>Perfil</th>
              <th>Revisión</th>
              <th>Fecha de subida</th>
              <th style={{ paddingRight: '1.5rem', textAlign: 'center' }}>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((document) => (
              <tr key={document.id}>
                <td style={{ paddingLeft: '1.5rem', fontWeight: 500 }}>
                  {document.original_filename || 'Sin nombre'}
                </td>
                <td style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>
                  {document.mime_type || 'Desconocido'}
                </td>
                <td>{formatFileSize(document.file_size)}</td>
                <td>
                  {document.profile_type && (
                    <span className={`badge badge-${getProfileBadgeType(document.profile_type)}`}>
                      {document.profile_type}
                    </span>
                  )}
                </td>
                <td>
                  <span
                    className={`badge ${
                      document.metadata?.review_status === 'accepted'
                        ? 'badge-success'
                        : document.metadata?.review_status === 'rejected'
                        ? 'badge-error'
                        : 'badge-warning'
                    }`}
                  >
                    {reviewLabel(document)}
                  </span>
                </td>
                <td>{new Date(document.uploaded_at).toLocaleDateString('es-ES')}</td>
                <td style={{ paddingRight: '1.5rem', textAlign: 'center' }}>
                  <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center', flexWrap: 'wrap' }}>
                    {document.public_url ? (
                      <a
                        href={document.public_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn btn-primary"
                        style={{
                          fontSize: '0.875rem',
                          padding: '0.5rem 1rem',
                          textDecoration: 'none',
                          display: 'inline-block'
                        }}
                      >
                        📥 Descargar
                      </a>
                    ) : (
                      <span style={{ color: 'var(--text-tertiary)', fontSize: '0.875rem' }}>
                        No disponible
                      </span>
                    )}
                    <button
                      className="btn btn-secondary"
                      style={{ fontSize: '0.8rem', padding: '0.45rem 0.75rem' }}
                      onClick={() => handleReview(document, 'accepted')}
                      disabled={reviewingId === document.id}
                    >
                      {reviewingId === document.id ? '...' : 'Aceptar'}
                    </button>
                    <button
                      className="btn btn-secondary"
                      style={{ fontSize: '0.8rem', padding: '0.45rem 0.75rem' }}
                      onClick={() => handleReview(document, 'rejected')}
                      disabled={reviewingId === document.id}
                    >
                      {reviewingId === document.id ? '...' : 'Rechazar'}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
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
