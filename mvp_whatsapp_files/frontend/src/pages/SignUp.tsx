import { FormEvent, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import ThemeToggle from '../components/ThemeToggle'

const APP_MODE = import.meta.env.VITE_APP_MODE || 'real'

export default function SignUp() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [name, setName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const navigate = useNavigate()

  const isMockMode = APP_MODE === 'mock'

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setSuccess(false)

    // Validation
    if (password !== confirmPassword) {
      setError('Passwords do not match')
      setLoading(false)
      return
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters')
      setLoading(false)
      return
    }

    try {
      if (isMockMode) {
        setError('Sign up is not available in mock mode. Please use one of the predefined users.')
        setLoading(false)
        return
      }

      // Real Supabase authentication
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            name: name || email.split('@')[0],
          }
        }
      })

      if (error) throw error

      // Check if email confirmation is required
      if (data?.user && !data.session) {
        setSuccess(true)
        setError('Please check your email to confirm your account before logging in.')
      } else {
        setSuccess(true)
        setTimeout(() => {
          navigate('/login', { replace: true })
        }, 2000)
      }
    } catch (err) {
      console.error('Sign up error:', err)
      setError(err instanceof Error ? err.message : 'An error occurred during sign up')
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
          Create Account
        </h2>
        
        {isMockMode && (
          <div className="alert alert-warning" style={{ marginBottom: '1.5rem' }}>
            <strong>⚠️ Mock Mode</strong>
            <p style={{ margin: '8px 0 0', fontSize: '0.875rem' }}>
              Sign up is not available in mock mode. Please use the <Link to="/login" style={{ color: 'var(--primary)', textDecoration: 'underline' }}>login page</Link> with predefined users.
            </p>
          </div>
        )}
        
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {error && !success && (
            <div className="alert alert-error">
              {error}
            </div>
          )}

          {success && (
            <div className="alert alert-success">
              ✅ Account created successfully! {error || 'Redirecting to login...'}
            </div>
          )}
          
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label htmlFor="name">
              Name (Optional)
            </label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Full name"
              disabled={isMockMode}
            />
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label htmlFor="email">
              Email *
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="your@email.com"
              disabled={isMockMode}
            />
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label htmlFor="password">
              Password *
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="At least 6 characters"
              disabled={isMockMode}
            />
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label htmlFor="confirmPassword">
              Confirm Password *
            </label>
            <input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              placeholder="Repeat password"
              disabled={isMockMode}
            />
          </div>

          <button
            type="submit"
            disabled={loading || isMockMode || success}
            className="btn btn-primary"
            style={{ 
              width: '100%',
              padding: '0.75rem',
              fontSize: '1rem'
            }}
          >
            {loading ? 'Creating account...' : 'Sign Up'}
          </button>

          <div style={{ textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
            Already have an account?{' '}
            <Link to="/login" style={{ color: 'var(--primary)', textDecoration: 'underline' }}>
              Sign in
            </Link>
          </div>
        </form>
      </div>
    </div>
  )
}
