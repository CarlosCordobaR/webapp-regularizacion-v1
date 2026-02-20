import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import ThemeToggle from '../components/ThemeToggle'

const APP_MODE = import.meta.env.VITE_APP_MODE || 'real'

const MOCK_USERS = [
  { id: '1', email: 'admin@mock.local', name: 'Admin User', role: 'admin' },
  { id: '2', email: 'lawyer1@mock.local', name: 'María García', role: 'lawyer' },
  { id: '3', email: 'lawyer2@mock.local', name: 'Carlos Rodríguez', role: 'lawyer' },
  { id: '4', email: 'assistant1@mock.local', name: 'Ana López', role: 'assistant' },
  { id: '5', email: 'viewer@mock.local', name: 'Guest Viewer', role: 'viewer' },
]

export default function LoginSimple() {
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleUserClick = (user: typeof MOCK_USERS[0]) => {
    console.log('🔵 User clicked:', user.name)
    setLoading(true)

    // Store user in localStorage
    localStorage.setItem('mock_user', JSON.stringify(user))
    console.log('✅ User stored in localStorage')

    // Navigate after small delay
    setTimeout(() => {
      console.log('🚀 Navigating to /clients')
      navigate('/clients', { replace: true })
    }, 200)
  }

  return (
    <div style={{ 
      minHeight: '100vh', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center',
      background: 'var(--bg-primary)',
      padding: '2rem'
    }}>
      <div style={{ position: 'absolute', top: '1.5rem', right: '1.5rem' }}>
        <ThemeToggle />
      </div>
      
      <div className="card" style={{ 
        maxWidth: '460px', 
        width: '100%',
        boxShadow: 'var(--shadow-lg)'
      }}>
        <h1 style={{ 
          fontSize: '1.875rem', 
          fontWeight: 700, 
          color: 'var(--text-primary)',
          marginBottom: '0.5rem',
          textAlign: 'center'
        }}>
          WhatsApp Client Manager
        </h1>
        <h2 style={{ 
          fontSize: '1.25rem', 
          fontWeight: 500, 
          color: 'var(--text-secondary)',
          marginBottom: '2rem',
          textAlign: 'center'
        }}>
          Login
        </h2>
        
        <div className="alert alert-warning" style={{ marginBottom: '1.5rem' }}>
          <strong>🧪 Mock Mode</strong>
          <p style={{ margin: '8px 0 0', fontSize: '0.875rem' }}>
            Development mode active. Click a user to login.
          </p>
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ fontSize: '1rem', marginBottom: '0.75rem', color: 'var(--text-primary)' }}>
            Select User:
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {MOCK_USERS.map(user => (
              <button
                key={user.id}
                onClick={() => handleUserClick(user)}
                disabled={loading}
                className="btn btn-secondary"
                style={{
                  width: '100%',
                  padding: '0.75rem 1rem',
                  textAlign: 'left',
                  justifyContent: 'flex-start',
                  opacity: loading ? 0.5 : 1,
                }}
              >
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                  <div style={{ fontWeight: 600 }}>{user.name}</div>
                  <div style={{ fontSize: '0.75rem', opacity: 0.7 }}>
                    {user.email} • {user.role}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {loading && (
          <div style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
            Logging in...
          </div>
        )}

        {APP_MODE === 'real' && (
          <div style={{ marginTop: '1.5rem', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.875rem', paddingTop: '1.5rem', borderTop: '1px solid var(--border-color)' }}>
            Don't have an account?{' '}
            <Link to="/signup" style={{ color: 'var(--primary)', textDecoration: 'underline', fontWeight: 600 }}>
              Sign up
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}
