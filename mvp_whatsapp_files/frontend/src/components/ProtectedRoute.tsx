import { Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

interface ProtectedRouteProps {
  children: React.ReactNode
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '100vh',
        background: 'var(--bg-primary)',
        color: 'var(--text-primary)'
      }}>
        <div className="spinner"></div>
        <span style={{ marginLeft: '1rem' }}>Loading...</span>
      </div>
    )
  }

  if (!user) {
    console.log('ProtectedRoute: No user, redirecting to login')
    return <Navigate to="/login" replace />
  }

  console.log('ProtectedRoute: User authenticated:', user.email)
  return <>{children}</>
}
