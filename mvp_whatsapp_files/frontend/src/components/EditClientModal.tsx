import { FormEvent, useEffect, useState } from 'react'
import { api, Client, CreateClientRequest } from '../lib/api'

interface EditClientModalProps {
  isOpen: boolean
  client: Client | null
  onClose: () => void
  onSuccess: () => void
}

const PROFILE_TYPES = [
  { value: 'OTHER', label: 'Other' },
  { value: 'ASYLUM', label: 'Asylum' },
  { value: 'ARRAIGO', label: 'Arraigo' },
  { value: 'STUDENT', label: 'Student' },
  { value: 'IRREGULAR', label: 'Irregular' },
] as const

const CLIENT_STATUSES = [
  { value: 'active', label: 'Activo' },
  { value: 'inactive', label: 'Inactivo' },
  { value: 'archived', label: 'Archivado' },
] as const

export default function EditClientModal({ isOpen, client, onClose, onSuccess }: EditClientModalProps) {
  const [formData, setFormData] = useState({
    full_name: '',
    phone_number: '',
    passport_or_nie: '',
    email: '',
    profile_type: 'OTHER' as CreateClientRequest['profile_type'],
    status: 'active' as CreateClientRequest['status'],
    notes: '',
  })
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})

  // Load client data when modal opens
  useEffect(() => {
    if (isOpen && client) {
      setFormData({
        full_name: client.name || '',
        phone_number: client.phone_number,
        passport_or_nie: client.passport_or_nie || '',
        email: client.email || '',
        profile_type: client.profile_type as CreateClientRequest['profile_type'],
        status: client.status as CreateClientRequest['status'],
        notes: client.notes || client.metadata?.notes || '',
      })
      setSelectedFiles([])
      setError(null)
      setFieldErrors({})
    }
  }, [isOpen, client])

  if (!isOpen || !client) return null

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {}

    // Validate full name (optional in edit)
    if (formData.full_name && !formData.full_name.trim()) {
      errors.full_name = 'Name cannot be empty if provided'
    }

    // Validate passport_or_nie (optional in edit)
    if (formData.passport_or_nie && !formData.passport_or_nie.trim()) {
      errors.passport_or_nie = 'Passport/NIE cannot be empty if provided'
    }

    // Validate phone number (optional in edit)
    if (formData.phone_number && formData.phone_number.trim()) {
      const phoneRegex = /^\+?\d{8,15}$/
      const cleanPhone = formData.phone_number.replace(/[\s\-()]/g, '')
      if (!phoneRegex.test(cleanPhone)) {
        errors.phone_number = 'Phone must contain 8-15 digits (e.g., +34600111222)'
      }
    }

    // Validate email (optional, but must be valid if provided)
    if (formData.email && formData.email.trim()) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      if (!emailRegex.test(formData.email.trim())) {
        errors.email = 'Invalid email format'
      }
    }

    setFieldErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files) return

    const newFiles: File[] = []
    const errors: string[] = []

    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      
      // Validate file type
      if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
        errors.push(`${file.name} no es un archivo PDF`)
        continue
      }

      // Validate file size (max 10MB)
      const maxSize = 10 * 1024 * 1024
      if (file.size > maxSize) {
        errors.push(`${file.name} excede el tamaño máximo de 10MB`)
        continue
      }

      newFiles.push(file)
    }

    if (errors.length > 0) {
      setError(errors.join('. '))
    } else {
      setError(null)
    }

    setSelectedFiles([...selectedFiles, ...newFiles])
    
    // Reset input
    e.target.value = ''
  }

  const handleRemoveFile = (index: number) => {
    setSelectedFiles(selectedFiles.filter((_, i) => i !== index))
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!validateForm()) {
      return
    }

    setLoading(true)

    try {
      // Only send fields that have changed or have values
      const updateData: Partial<CreateClientRequest> = {}
      
      if (formData.full_name.trim() !== client.name) {
        updateData.full_name = formData.full_name.trim()
      }
      
      if (formData.phone_number.trim() !== client.phone_number) {
        updateData.phone_number = formData.phone_number.trim()
      }
      
      if (formData.passport_or_nie.trim() !== client.passport_or_nie) {
        updateData.passport_or_nie = formData.passport_or_nie.trim()
      }
      
      if (formData.profile_type !== client.profile_type) {
        updateData.profile_type = formData.profile_type
      }
      
      if (formData.status !== client.status) {
        updateData.status = formData.status
      }
      
      const currentEmail = client.email || ''
      if (formData.email.trim() !== currentEmail) {
        updateData.email = formData.email.trim()
      }
      
      const currentNotes = client.notes || client.metadata?.notes || ''
      if (formData.notes.trim() !== currentNotes) {
        updateData.notes = formData.notes.trim()
      }

      await api.updateClient(client.id, updateData, selectedFiles)

      // Reset form
      setSelectedFiles([])
      setFieldErrors({})

      // Notify parent
      onSuccess()
      onClose()
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update client'
      
      // Check for specific error types
      if (errorMessage.includes('already exists')) {
        setFieldErrors({ phone_number: errorMessage })
      } else {
        setError(errorMessage)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    if (!loading) {
      setSelectedFiles([])
      setError(null)
      setFieldErrors({})
      onClose()
    }
  }

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: '1rem',
      }}
      onClick={handleClose}
    >
      <div
        className="card"
        style={{
          maxWidth: '600px',
          width: '100%',
          maxHeight: '90vh',
          overflow: 'auto',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
            ✏️ Editar Cliente
          </h2>
          <button
            onClick={handleClose}
            disabled={loading}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '1.5rem',
              cursor: loading ? 'not-allowed' : 'pointer',
              color: 'var(--text-secondary)',
              padding: '0.25rem',
            }}
          >
            ×
          </button>
        </div>

        {error && (
          <div className="alert alert-error" style={{ marginBottom: '1rem' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Client ID (read-only) */}
          <div style={{ marginBottom: '1rem', padding: '0.75rem', backgroundColor: 'var(--bg-secondary)', borderRadius: '0.375rem', border: '1px solid var(--border)' }}>
            <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.75rem', fontWeight: 500, color: 'var(--text-secondary)' }}>
              ID Cliente
            </label>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <code style={{ fontSize: '0.875rem', fontFamily: 'monospace', color: 'var(--text-primary)', flex: 1 }}>
                {client.id}
              </code>
              <button
                type="button"
                onClick={() => {
                  navigator.clipboard.writeText(client.id)
                  alert('ID copiado al portapapeles')
                }}
                style={{
                  padding: '0.25rem 0.5rem',
                  fontSize: '0.75rem',
                  border: '1px solid var(--border)',
                  borderRadius: '0.25rem',
                  backgroundColor: 'var(--bg-primary)',
                  color: 'var(--text-primary)',
                  cursor: 'pointer',
                }}
              >
                📋 Copiar
              </button>
            </div>
          </div>

          {/* Full Name */}
          <div style={{ marginBottom: '1rem' }}>
            <label htmlFor="full_name" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>
              Nombre completo
            </label>
            <input
              type="text"
              id="full_name"
              value={formData.full_name}
              onChange={(e) => {
                setFormData({ ...formData, full_name: e.target.value })
                if (fieldErrors.full_name) {
                  setFieldErrors({ ...fieldErrors, full_name: '' })
                }
              }}
              disabled={loading}
              placeholder="Juan Pérez"
              style={{
                width: '100%',
                padding: '0.75rem',
                border: fieldErrors.full_name ? '1px solid var(--danger)' : '1px solid var(--border)',
                borderRadius: '0.375rem',
                backgroundColor: 'var(--bg-primary)',
                color: 'var(--text-primary)',
              }}
            />
            {fieldErrors.full_name && (
              <p style={{ color: 'var(--danger)', fontSize: '0.875rem', marginTop: '0.25rem' }}>
                {fieldErrors.full_name}
              </p>
            )}
          </div>

          {/* Passport/NIE */}
          <div style={{ marginBottom: '1rem' }}>
            <label htmlFor="passport_or_nie" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>
              Pasaporte/NIE
            </label>
            <input
              type="text"
              id="passport_or_nie"
              value={formData.passport_or_nie}
              onChange={(e) => {
                setFormData({ ...formData, passport_or_nie: e.target.value })
                if (fieldErrors.passport_or_nie) {
                  setFieldErrors({ ...fieldErrors, passport_or_nie: '' })
                }
              }}
              disabled={loading}
              placeholder="X1234567A o AB123456"
              style={{
                width: '100%',
                padding: '0.75rem',
                border: fieldErrors.passport_or_nie ? '1px solid var(--danger)' : '1px solid var(--border)',
                borderRadius: '0.375rem',
                backgroundColor: 'var(--bg-primary)',
                color: 'var(--text-primary)',
              }}
            />
            {fieldErrors.passport_or_nie && (
              <p style={{ color: 'var(--danger)', fontSize: '0.875rem', marginTop: '0.25rem' }}>
                {fieldErrors.passport_or_nie}
              </p>
            )}
          </div>

          {/* Phone Number */}
          <div style={{ marginBottom: '1rem' }}>
            <label htmlFor="phone_number" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>
              Teléfono
            </label>
            <input
              type="text"
              id="phone_number"
              value={formData.phone_number}
              onChange={(e) => {
                setFormData({ ...formData, phone_number: e.target.value })
                if (fieldErrors.phone_number) {
                  setFieldErrors({ ...fieldErrors, phone_number: '' })
                }
              }}
              disabled={loading}
              placeholder="+34 600 111 222"
              style={{
                width: '100%',
                padding: '0.75rem',
                border: fieldErrors.phone_number ? '1px solid var(--danger)' : '1px solid var(--border)',
                borderRadius: '0.375rem',
                backgroundColor: 'var(--bg-primary)',
                color: 'var(--text-primary)',
              }}
            />
            {fieldErrors.phone_number && (
              <p style={{ color: 'var(--danger)', fontSize: '0.875rem', marginTop: '0.25rem' }}>
                {fieldErrors.phone_number}
              </p>
            )}
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginTop: '0.25rem' }}>
              Formato: +34 XXX XXX XXX (8-15 dígitos)
            </p>
          </div>

          {/* Email */}
          <div style={{ marginBottom: '1rem' }}>
            <label htmlFor="email" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>
              Email (opcional)
            </label>
            <input
              type="email"
              id="email"
              value={formData.email}
              onChange={(e) => {
                setFormData({ ...formData, email: e.target.value })
                if (fieldErrors.email) {
                  setFieldErrors({ ...fieldErrors, email: '' })
                }
              }}
              disabled={loading}
              placeholder="email@ejemplo.com"
              style={{
                width: '100%',
                padding: '0.75rem',
                border: fieldErrors.email ? '1px solid var(--danger)' : '1px solid var(--border)',
                borderRadius: '0.375rem',
                backgroundColor: 'var(--bg-primary)',
                color: 'var(--text-primary)',
              }}
            />
            {fieldErrors.email && (
              <p style={{ color: 'var(--danger)', fontSize: '0.875rem', marginTop: '0.25rem' }}>
                {fieldErrors.email}
              </p>
            )}
          </div>

          {/* Profile Type */}
          <div style={{ marginBottom: '1rem' }}>
            <label htmlFor="profile_type" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>
              Tipo de perfil
            </label>
            <select
              id="profile_type"
              value={formData.profile_type}
              onChange={(e) => setFormData({ ...formData, profile_type: e.target.value as any })}
              disabled={loading}
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid var(--border)',
                borderRadius: '0.375rem',
                backgroundColor: 'var(--bg-primary)',
                color: 'var(--text-primary)',
              }}
            >
              {PROFILE_TYPES.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          {/* Status */}
          <div style={{ marginBottom: '1rem' }}>
            <label htmlFor="status" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>
              Estado
            </label>
            <select
              id="status"
              value={formData.status}
              onChange={(e) => setFormData({ ...formData, status: e.target.value as any })}
              disabled={loading}
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid var(--border)',
                borderRadius: '0.375rem',
                backgroundColor: 'var(--bg-primary)',
                color: 'var(--text-primary)',
              }}
            >
              {CLIENT_STATUSES.map((status) => (
                <option key={status.value} value={status.value}>
                  {status.label}
                </option>
              ))}
            </select>
          </div>

          {/* Documents Upload */}
          <div style={{ marginBottom: '1rem' }}>
            <label htmlFor="documents" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>
              Agregar documentos PDF (opcional)
            </label>
            <div
              style={{
                border: '2px dashed var(--border)',
                borderRadius: '0.375rem',
                padding: '1rem',
                textAlign: 'center',
                backgroundColor: 'var(--bg-secondary)',
              }}
            >
              <input
                type="file"
                id="documents"
                accept="application/pdf,.pdf"
                multiple
                onChange={handleFileSelect}
                disabled={loading}
                style={{ display: 'none' }}
              />
              <label
                htmlFor="documents"
                style={{
                  cursor: loading ? 'not-allowed' : 'pointer',
                  color: 'var(--primary)',
                  fontWeight: 500,
                  display: 'inline-block',
                }}
              >
                📎 Seleccionar archivos PDF
              </label>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '0.5rem', marginBottom: 0 }}>
                Máximo 10MB por archivo
              </p>
            </div>

            {/* Selected Files List */}
            {selectedFiles.length > 0 && (
              <div style={{ marginTop: '1rem' }}>
                <p style={{ fontSize: '0.875rem', fontWeight: 500, marginBottom: '0.5rem' }}>
                  Archivos seleccionados ({selectedFiles.length}):
                </p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {selectedFiles.map((file, index) => (
                    <div
                      key={index}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '0.5rem',
                        backgroundColor: 'var(--bg-secondary)',
                        borderRadius: '0.375rem',
                        border: '1px solid var(--border)',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: 1, minWidth: 0 }}>
                        <span>📄</span>
                        <span
                          style={{
                            fontSize: '0.875rem',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                          }}
                          title={file.name}
                        >
                          {file.name}
                        </span>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', flexShrink: 0 }}>
                          ({(file.size / 1024).toFixed(1)} KB)
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleRemoveFile(index)}
                        disabled={loading}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: 'var(--danger)',
                          cursor: loading ? 'not-allowed' : 'pointer',
                          padding: '0.25rem 0.5rem',
                          fontSize: '1.25rem',
                        }}
                        title="Eliminar archivo"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Notes */}
          <div style={{ marginBottom: '1.5rem' }}>
            <label htmlFor="notes" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>
              Notas
            </label>
            <textarea
              id="notes"
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              disabled={loading}
              placeholder="Información adicional sobre el cliente..."
              rows={3}
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid var(--border)',
                borderRadius: '0.375rem',
                backgroundColor: 'var(--bg-primary)',
                color: 'var(--text-primary)',
                resize: 'vertical',
              }}
            />
          </div>

          {/* Buttons */}
          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
            <button
              type="button"
              onClick={handleClose}
              disabled={loading}
              className="btn btn-secondary"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="btn btn-primary"
              style={{ minWidth: '120px' }}
            >
              {loading ? (
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <div className="spinner" style={{ width: '16px', height: '16px' }}></div>
                  Guardando...
                </span>
              ) : (
                '💾 Guardar Cambios'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
