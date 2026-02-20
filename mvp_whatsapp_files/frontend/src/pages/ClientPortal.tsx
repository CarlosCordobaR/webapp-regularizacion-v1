import { FormEvent, useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api, Document, PortalChecklistItem, PortalExpedienteResponse } from '../lib/api'
import AppHeader from '../components/AppHeader'

function statusBadge(status: PortalChecklistItem['status']): string {
  const map = {
    missing: 'warning',
    uploaded: 'info',
    accepted: 'success',
    rejected: 'error',
  }
  return map[status] || 'info'
}

export default function ClientPortal() {
  const { id } = useParams<{ id: string }>()
  const [phone, setPhone] = useState('')
  const [passport, setPassport] = useState('')
  const [token, setToken] = useState<string | null>(null)
  const [data, setData] = useState<PortalExpedienteResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [exporting, setExporting] = useState(false)

  const storageKey = useMemo(() => (id ? `portal_token_${id}` : null), [id])

  useEffect(() => {
    if (!storageKey) return
    const saved = sessionStorage.getItem(storageKey)
    if (saved) {
      setToken(saved)
    }
  }, [storageKey])

  useEffect(() => {
    if (!id || !token) return
    void loadExpediente(id, token)
  }, [id, token])

  const loadExpediente = async (clientId: string, currentToken: string) => {
    try {
      setLoading(true)
      setError(null)
      const result = await api.getPortalExpediente(clientId, currentToken)
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo cargar el expediente')
      setData(null)
      if (storageKey) sessionStorage.removeItem(storageKey)
      setToken(null)
    } finally {
      setLoading(false)
    }
  }

  const handleLogin = async (e: FormEvent) => {
    e.preventDefault()
    if (!id) return
    try {
      setLoading(true)
      setError(null)
      const auth = await api.portalAuth(id, phone.trim(), passport.trim())
      setToken(auth.token)
      if (storageKey) {
        sessionStorage.setItem(storageKey, auth.token)
      }
      await loadExpediente(id, auth.token)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Acceso denegado')
    } finally {
      setLoading(false)
    }
  }

  const logout = () => {
    if (storageKey) sessionStorage.removeItem(storageKey)
    setToken(null)
    setData(null)
    setError(null)
    setPhone('')
    setPassport('')
  }

  const downloadExpediente = async () => {
    if (!id || !token) return
    try {
      setExporting(true)
      setError(null)
      const exportJob = await api.createExportJob(
        id,
        { acceptedOnly: true, expiresIn: 1800, requestedBy: 'client' },
        token
      )
      if (!exportJob.signed_url) {
        throw new Error('No se obtuvo URL de descarga del expediente')
      }
      const { blob, filename } = await api.downloadFromSignedUrl(
        exportJob.signed_url,
        exportJob.filename || 'expediente.zip'
      )
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo descargar expediente')
    } finally {
      setExporting(false)
    }
  }

  if (!id) {
    return (
      <div className="page-container">
        <div className="alert alert-error">Portal inválido: falta ID de cliente.</div>
      </div>
    )
  }

  if (!token || !data) {
    return (
      <>
        <AppHeader />
        <div className="page-container" style={{ maxWidth: '520px' }}>
          <div className="card">
            <h1 style={{ marginBottom: '0.5rem' }}>Portal Cliente</h1>
            <p style={{ marginBottom: '1rem', color: 'var(--text-secondary)' }}>
              Accede a tu expediente con tu teléfono y pasaporte/NIE.
            </p>
            {error && <div className="alert alert-error" style={{ marginBottom: '1rem' }}>{error}</div>}
            <form onSubmit={handleLogin} style={{ display: 'grid', gap: '0.9rem' }}>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label htmlFor="phone">Teléfono</label>
                <input
                  id="phone"
                  type="text"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+34 600 111 222"
                  required
                />
              </div>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label htmlFor="passport">Pasaporte / NIE</label>
                <input
                  id="passport"
                  type="text"
                  value={passport}
                  onChange={(e) => setPassport(e.target.value)}
                  placeholder="X1234567A"
                  required
                />
              </div>
              <button className="btn btn-primary" type="submit" disabled={loading}>
                {loading ? 'Verificando...' : 'Entrar al expediente'}
              </button>
            </form>
          </div>
        </div>
      </>
    )
  }

  return (
    <>
      <AppHeader />
      <div className="page-container">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div>
            <h1 style={{ marginBottom: '0.35rem' }}>Mi Expediente</h1>
            <p style={{ color: 'var(--text-secondary)' }}>
              {data.client.name || 'Cliente'} · {data.client.profile_type || 'Sin perfil'}
            </p>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button className="btn btn-primary" onClick={downloadExpediente} disabled={exporting}>
              {exporting ? 'Generando ZIP...' : 'Descargar expediente'}
            </button>
            <button className="btn btn-secondary" onClick={logout}>Cerrar sesión</button>
          </div>
        </div>

        {loading && (
          <div className="card">
            <div className="spinner" />
          </div>
        )}
        {error && <div className="alert alert-error" style={{ marginBottom: '1rem' }}>{error}</div>}

        <div className="card" style={{ marginBottom: '1rem' }}>
          <h2 style={{ fontSize: '1.1rem', marginBottom: '0.8rem' }}>Checklist documental</h2>
          <div style={{ display: 'grid', gap: '0.65rem' }}>
            {data.checklist.map((item) => (
              <div
                key={item.type}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  gap: '0.75rem',
                  border: '1px solid var(--border)',
                  borderRadius: '8px',
                  padding: '0.7rem 0.8rem',
                  backgroundColor: 'var(--bg-secondary)',
                }}
              >
                <div>
                  <div style={{ fontWeight: 600 }}>{item.label}</div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.86rem' }}>{item.message}</div>
                </div>
                <span className={`badge badge-${statusBadge(item.status)}`}>{item.status}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div className="table-container" style={{ margin: 0 }}>
            <table>
              <thead>
                <tr>
                  <th style={{ paddingLeft: '1rem' }}>Archivo</th>
                  <th>Tipo</th>
                  <th>Revisión</th>
                  <th>Fecha</th>
                  <th style={{ paddingRight: '1rem' }}>Acción</th>
                </tr>
              </thead>
              <tbody>
                {data.documents.map((doc: Document) => (
                  <tr key={doc.id}>
                    <td style={{ paddingLeft: '1rem' }}>{doc.original_filename || 'Sin nombre'}</td>
                    <td>{doc.document_type || 'Sin tipo'}</td>
                    <td>{(doc.metadata?.review_status as string) || 'pending'}</td>
                    <td>{new Date(doc.uploaded_at).toLocaleDateString('es-ES')}</td>
                    <td style={{ paddingRight: '1rem' }}>
                      {doc.public_url ? (
                        <a href={doc.public_url} target="_blank" rel="noreferrer" className="btn btn-primary" style={{ fontSize: '0.85rem' }}>
                          Descargar
                        </a>
                      ) : (
                        <span style={{ color: 'var(--text-tertiary)' }}>No disponible</span>
                      )}
                    </td>
                  </tr>
                ))}
                {data.documents.length === 0 && (
                  <tr>
                    <td colSpan={5} style={{ padding: '1rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
                      Aún no hay documentos cargados.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </>
  )
}
