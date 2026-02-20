import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import ThemeToggle from './ThemeToggle'

interface AppHeaderProps {
  title?: string
  showSignOut?: boolean
}

export default function AppHeader({ title = 'WhatsApp Client Manager', showSignOut = true }: AppHeaderProps) {
  const navigate = useNavigate()
  const { signOut } = useAuth()

  const handleSignOut = async () => {
    console.log('🔴 Signing out')
    try {
      await signOut()
      navigate('/login', { replace: true })
    } catch (error) {
      console.error('Sign out error:', error)
    }
  }

  return (
    <header className="app-header">
      <div className="header-content">
        <h1 className="header-title">{title}</h1>
        <div className="header-actions">
          <ThemeToggle />
          {showSignOut && (
            <button onClick={handleSignOut} className="btn btn-secondary">
              Sign Out
            </button>
          )}
        </div>
      </div>
    </header>
  )
}
