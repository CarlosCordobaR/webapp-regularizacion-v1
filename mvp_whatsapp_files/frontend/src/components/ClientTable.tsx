import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, Client } from '../lib/api'

interface ClientTableProps {
  clients: Client[]
}

export default function ClientTable({ clients }: ClientTableProps) {
  const navigate = useNavigate()
  const [generatingExpediente, setGeneratingExpediente] = useState<string | null>(null)

  const handleGenerateExpediente = async (e: React.MouseEvent, clientId: string) => {
    e.stopPropagation()
    
    setGeneratingExpediente(clientId)
    
    try {
      const exportJob = await api.createExportJob(clientId, {
        acceptedOnly: true,
        expiresIn: 3600,
        requestedBy: 'staff',
      })
      if (!exportJob.signed_url) {
        throw new Error('La exportación se generó, pero no devolvió URL de descarga')
      }
      const { blob, filename } = await api.downloadFromSignedUrl(
        exportJob.signed_url,
        exportJob.filename || 'expediente.zip'
      )
      
      // Create download link
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      
      // Cleanup
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      
    } catch (err: any) {
      let errorMessage = 'Error al generar expediente'
      
      if (err instanceof Error) {
        errorMessage = err.message
      } else if (typeof err === 'string') {
        errorMessage = err
      } else if (err && typeof err === 'object') {
        // Handle object errors
        errorMessage = err.message || err.detail || err.error || JSON.stringify(err)
      }
      
      alert(errorMessage)
    } finally {
      setGeneratingExpediente(null)
    }
  }

  if (clients.length === 0) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
        <p style={{ color: 'var(--text-secondary)' }}>No clients found</p>
      </div>
    )
  }

  return (
    <div className="table-container">
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Phone</th>
            <th>Email</th>
            <th>Profile Type</th>
            <th>Status</th>
            <th>Created</th>
            <th style={{ textAlign: 'center' }}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {clients.map((client) => (
            <tr
              key={client.id}
              style={{ cursor: 'pointer' }}
              onClick={() => navigate(`/clients/${client.id}`)}
            >
              <td>{client.name || 'Unknown'}</td>
              <td>{client.phone_number}</td>
              <td style={{ color: client.email ? 'var(--text-primary)' : 'var(--text-secondary)', fontStyle: client.email ? 'normal' : 'italic' }}>
                {client.email || '—'}
              </td>
              <td>
                <span className={`badge badge-${getProfileBadgeType(client.profile_type)}`}>
                  {client.profile_type}
                </span>
              </td>
              <td style={{ textTransform: 'capitalize' }}>{client.status.toLowerCase()}</td>
              <td>{new Date(client.created_at).toLocaleDateString()}</td>
              <td>
                <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      navigate(`/clients/${client.id}`)
                    }}
                    className="btn btn-primary"
                    style={{ fontSize: '0.875rem', padding: '0.5rem 1rem' }}
                  >
                    View
                  </button>
                  <button
                    onClick={(e) => handleGenerateExpediente(e, client.id)}
                    disabled={generatingExpediente === client.id}
                    className="btn btn-secondary"
                    style={{ 
                      fontSize: '0.875rem', 
                      padding: '0.5rem 1rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem'
                    }}
                    title="Generar expediente ZIP con documentos requeridos"
                  >
                    {generatingExpediente === client.id ? (
                      <>⏳ Generando...</>
                    ) : (
                      <>📦 Expediente</>
                    )}
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
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
