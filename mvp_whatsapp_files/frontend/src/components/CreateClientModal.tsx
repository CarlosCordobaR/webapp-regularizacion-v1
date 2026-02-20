import { FormEvent, useState } from 'react'
import { api, CreateClientRequest } from '../lib/api'

interface FileWithType {
  file: File
  documentType: 'TASA' | 'PASSPORT_NIE' | null
}

interface CreateClientModalProps {
  isOpen: boolean
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

export default function CreateClientModal({ isOpen, onClose, onSuccess }: CreateClientModalProps) {
  const [formData, setFormData] = useState({
    full_name: '',
    phone_number: '',
    passport_or_nie: '',
    email: '',
    profile_type: 'OTHER' as CreateClientRequest['profile_type'],
    notes: '',
  })
  const [selectedFiles, setSelectedFiles] = useState<FileWithType[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})

  if (!isOpen) return null

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {}

    // Validate full name
    if (!formData.full_name.trim()) {
      errors.full_name = 'Name is required'
    }

    // Validate phone number
    if (!formData.phone_number.trim()) {
      errors.phone_number = 'Phone number is required'
    } else {
      // Basic phone validation: 8-15 digits, optional '+'
      const phoneRegex = /^\+?\d{8,15}$/
      const cleanPhone = formData.phone_number.replace(/[\s\-()]/g, '')
      if (!phoneRegex.test(cleanPhone)) {
        errors.phone_number = 'Phone must contain 8-15 digits (e.g., +34600111222)'
      }
    }

    // Validate passport or NIE
    if (!formData.passport_or_nie.trim()) {
      errors.passport_or_nie = 'Passport or NIE is required'
    }

    // Validate email (optional, but must be valid if provided)
    if (formData.email.trim()) {
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

    const newFiles: FileWithType[] = []
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

      newFiles.push({ file, documentType: null })
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

  const handleDocumentTypeChange = (index: number, value: string) => {
    const updated = [...selectedFiles]
    // Convert empty string to null, otherwise use the value
    updated[index].documentType = value === '' ? null : (value as 'TASA' | 'PASSPORT_NIE')
    setSelectedFiles(updated)
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!validateForm()) {
      return
    }

    setLoading(true)

    try {
      const requestData: CreateClientRequest = {
        full_name: formData.full_name.trim(),
        phone_number: formData.phone_number.trim(),
        passport_or_nie: formData.passport_or_nie.trim(),
        profile_type: formData.profile_type,
      }

      if (formData.email.trim()) {
        requestData.email = formData.email.trim()
      }

      if (formData.notes.trim()) {
        requestData.notes = formData.notes.trim()
      }

      // Extract files and document types
      const files = selectedFiles.map(f => f.file)
      const documentTypes = selectedFiles.map(f => f.documentType)
      
      // STRICT VALIDATION: Block submission if files uploaded without types
      const untypedFiles = selectedFiles.filter(f => !f.documentType)
      if (untypedFiles.length > 0) {
        const fileNames = untypedFiles.map(f => f.file.name).join(', ')
        setError(`Por favor, selecciona el tipo para todos los documentos: ${fileNames}`)
        setLoading(false)
        return
      }
      
      // Debug logging (will remove after confirming fix)
      if (selectedFiles.length > 0) {
        console.log('📤 Enviando documentos:', selectedFiles.map(f => ({
          name: f.file.name,
          type: f.documentType || 'SIN TIPO'
        })))
        console.log('📋 Array documentTypes:', documentTypes)
      }

      await api.createClient(requestData, files, documentTypes)

      // Reset form
      setFormData({
        full_name: '',
        phone_number: '',
        passport_or_nie: '',
        email: '',
        profile_type: 'OTHER',
        notes: '',
      })
      setSelectedFiles([])
      setFieldErrors({})

      // Notify parent
      onSuccess()
      onClose()
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create client'
      
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
      setFormData({
        full_name: '',
        phone_number: '',
        passport_or_nie: '',
        email: '',
        profile_type: 'OTHER',
        notes: '',
      })
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
          maxWidth: '500px',
          width: '100%',
          maxHeight: '90vh',
          overflow: 'auto',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
            Crear Nuevo Cliente
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
          {/* Full Name */}
          <div style={{ marginBottom: '1rem' }}>
            <label htmlFor="full_name" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>
              Nombre completo <span style={{ color: 'var(--danger)' }}>*</span>
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

          {/* Phone Number */}
          <div style={{ marginBottom: '1rem' }}>
            <label htmlFor="phone_number" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>
              Teléfono <span style={{ color: 'var(--danger)' }}>*</span>
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

          {/* Passport or NIE */}
          <div style={{ marginBottom: '1rem' }}>
            <label htmlFor="passport_or_nie" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>
              Número de Pasaporte o NIE <span style={{ color: 'var(--danger)' }}>*</span>
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
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginTop: '0.25rem' }}>
              NIE español (ej: X1234567A) o número de pasaporte
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

          {/* Documents Upload */}
          <div style={{ marginBottom: '1rem' }}>
            <label htmlFor="documents" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>
              Documentos PDF (opcional)
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
                  {selectedFiles.map((fileWithType, index) => (
                    <div
                      key={index}
                      style={{
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.5rem',
                        padding: '0.75rem',
                        backgroundColor: 'var(--bg-secondary)',
                        borderRadius: '0.375rem',
                        border: '1px solid var(--border)',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: 1, minWidth: 0 }}>
                          <span>📄</span>
                          <span
                            style={{
                              fontSize: '0.875rem',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                            }}
                            title={fileWithType.file.name}
                          >
                            {fileWithType.file.name}
                          </span>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', flexShrink: 0 }}>
                            ({(fileWithType.file.size / 1024).toFixed(1)} KB)
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
                      
                      {/* Document Type Selection */}
                      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                        <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', flexShrink: 0 }}>
                          Tipo de documento:
                        </label>
                        <select
                          value={fileWithType.documentType || ''}
                          onChange={(e) => handleDocumentTypeChange(index, e.target.value)}
                          disabled={loading}
                          style={{
                            padding: '0.25rem 0.5rem',
                            fontSize: '0.75rem',
                            border: fileWithType.documentType ? '1px solid var(--border)' : '2px solid #ff9800',
                            borderRadius: '0.25rem',
                            backgroundColor: fileWithType.documentType ? 'var(--bg-primary)' : '#fff3e0',
                            color: fileWithType.documentType ? 'var(--text-primary)' : '#e65100',
                            flex: 1,
                            fontWeight: fileWithType.documentType ? 'normal' : 'bold',
                          }}
                        >
                          <option value="">⚠️ Selecciona un tipo (requerido)</option>
                          <option value="TASA">Tasa</option>
                          <option value="PASSPORT_NIE">Pasaporte/NIE</option>
                        </select>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Notes */}
          <div style={{ marginBottom: '1.5rem' }}>
            <label htmlFor="notes" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>
              Notas (opcional)
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
              style={{ minWidth: '100px' }}
            >
              {loading ? (
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <div className="spinner" style={{ width: '16px', height: '16px' }}></div>
                  Creando...
                </span>
              ) : (
                'Crear Cliente'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
