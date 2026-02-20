import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { MOCK_USERS } from '../lib/mockAuth'
import ThemeToggle from '../components/ThemeToggle'

const APP_MODE = import.meta.env.VITE_APP_MODE || 'real'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()
  const { signIn } = useAuth()

  const isMockMode = APP_MODE === 'mock'

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      await signIn(email, password)
      console.log('Login successful, navigating to /clients')
      navigate('/clients', { replace: true })
    } catch (err) {
      console.error('Login error:', err)
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const quickLogin = async (userEmail: string) => {
    if (loading) return
    
    setLoading(true)
    setError(null)

    try {
      await signIn(userEmail)
      console.log('Quick login successful, navigating to /clients')
      navigate('/clients', { replace: true })
    } catch (err) {
      console.error('Quick login error:', err)
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setLoading(false)
    }
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
        
        {isMockMode && (
          <div className="alert alert-warning" style={{ marginBottom: '1.5rem' }}>
            <strong>🧪 Mock Mode</strong>
            <p style={{ margin: '8px 0 0', fontSize: '0.875rem' }}>
              Development mode active. Select a user below or enter email only.
            </p>
          </div>
        )}

        {isMockMode && (
          <div style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ fontSize: '1rem', marginBottom: '0.75rem', color: 'var(--text-primary)' }}>
              Quick Select:
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {MOCK_USERS.map(user => (
                <button
                  key={user.id}
                  type="button"
                  onClick={() => quickLogin(user.email)}
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
            
            <div style={{ 
              textAlign: 'center', 
              margin: '1rem 0', 
              color: 'var(--text-tertiary)',
              fontSize: '0.875rem'
            }}>
              — or —
            </div>
          </div>
        )}
        
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {error && (
            <div className="alert alert-error">
              {error}
            </div>
          )}
          
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label htmlFor="email">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder={isMockMode ? 'Enter any mock user email' : 'your@email.com'}
            />
          </div>

          {!isMockMode && (
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label htmlFor="password">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="••••••••"
              />
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="btn btn-primary"
            style={{ 
              width: '100%',
              padding: '0.75rem',
              fontSize: '1rem'
            }}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        {!isMockMode && (
          <div style={{ marginTop: '1.5rem', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.875rem', paddingTop: '1.5rem', borderTop: '1px solid var(--border-color)' }}>
            Don't have an account?{' '}
            <a href="/signup" style={{ color: 'var(--primary)', textDecoration: 'underline', fontWeight: 600 }}>
              Sign up
            </a>
          </div>
        )}
      </div>
    </div>
  )
}
