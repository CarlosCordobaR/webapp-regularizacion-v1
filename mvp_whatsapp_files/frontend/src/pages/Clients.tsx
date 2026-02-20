import { useEffect, useState } from 'react'
import AppHeader from '../components/AppHeader'
import ClientTable from '../components/ClientTable.tsx'
import CreateClientModal from '../components/CreateClientModal'
import { api, Client } from '../lib/api'

export default function Clients() {
  const [clients, setClients] = useState<Client[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  const pageSize = 50

  useEffect(() => {
    // Auth will be handled by App.tsx routing
    loadClients()
  }, [page])

  const loadClients = async () => {
    try {
      setLoading(true)
      const response = await api.getClients(page, pageSize)
      setClients(response.data)
      setTotal(response.total)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load clients')
    } finally {
      setLoading(false)
    }
  }

  const handleClientCreated = async () => {
    // Show success message
    setSuccessMessage('Cliente creado exitosamente')
    setTimeout(() => setSuccessMessage(null), 3000)
    
    // Reload clients list to show new client
    await loadClients()
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

  const totalPages = Math.ceil(total / pageSize)

  return (
    <>
      <AppHeader />
      <div className="page-container">
        {successMessage && (
          <div className="alert alert-success" style={{ marginBottom: '1rem' }}>
            {successMessage}
          </div>
        )}

        <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 className="page-title">Clients</h2>
            <p className="page-subtitle">Total: {total} clients</p>
          </div>
          <button
            onClick={() => setIsModalOpen(true)}
            className="btn btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
          >
            <span>+</span>
            Crear Cliente
          </button>
        </div>

        <ClientTable clients={clients} />

        {totalPages > 1 && (
          <div className="pagination">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="btn btn-secondary"
            >
              Previous
            </button>
            <span className="page-info">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="btn btn-secondary"
            >
              Next
            </button>
          </div>
        )}
      </div>

      <CreateClientModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={handleClientCreated}
      />
    </>
  )
}
