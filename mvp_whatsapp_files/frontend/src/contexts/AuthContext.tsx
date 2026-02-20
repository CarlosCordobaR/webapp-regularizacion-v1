import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { User } from '@supabase/supabase-js'
import { supabase } from '../lib/supabase'
import { mockAuthService } from '../lib/mockAuth'

const APP_MODE = import.meta.env.VITE_APP_MODE || 'real'

interface AuthContextType {
  user: User | null
  loading: boolean
  signIn: (email: string, password?: string) => Promise<void>
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check active session on mount
    if (APP_MODE === 'mock') {
      // Mock mode: check localStorage
      const mockUser = mockAuthService.getCurrentUser()
      if (mockUser) {
        setUser({
          id: mockUser.id,
          email: mockUser.email,
          app_metadata: {},
          user_metadata: { name: mockUser.name, role: mockUser.role },
          aud: 'authenticated',
          created_at: new Date().toISOString(),
        } as User)
      }
      setLoading(false)
    } else {
      // Real mode: check Supabase session
      supabase.auth.getSession().then(({ data: { session } }) => {
        setUser(session?.user ?? null)
        setLoading(false)
      })

      // Listen for auth changes
      const {
        data: { subscription },
      } = supabase.auth.onAuthStateChange((_event, session) => {
        setUser(session?.user ?? null)
      })

      return () => subscription.unsubscribe()
    }
  }, [])

  const signIn = async (email: string, password?: string) => {
    if (APP_MODE === 'mock') {
      const mockResult = await mockAuthService.signIn(email)
      setUser({
        id: mockResult.user.id,
        email: mockResult.user.email,
        app_metadata: {},
        user_metadata: { name: mockResult.user.name, role: mockResult.user.role },
        aud: 'authenticated',
        created_at: new Date().toISOString(),
      } as User)
    } else {
      if (!password) throw new Error('Password required for real mode')
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      })
      if (error) throw error
      setUser(data.user)
    }
  }

  const signOut = async () => {
    if (APP_MODE === 'mock') {
      mockAuthService.signOut()
      setUser(null)
    } else {
      await supabase.auth.signOut()
      setUser(null)
    }
  }

  return (
    <AuthContext.Provider value={{ user, loading, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
