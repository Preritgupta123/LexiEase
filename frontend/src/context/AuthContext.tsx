import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react'
import type { Session, User } from '@supabase/supabase-js'
import { supabase } from '../lib/supabaseClient'

/**
 * Shape of the data our AuthContext provides to the rest of the app.
 */
interface AuthContextType {
  user: User | null
  session: Session | null
  loading: boolean
}

// Create the context with an initial undefined value.
// We enforce usage only through the useAuth() hook below,
// which throws a clear error if used incorrectly.
const AuthContext = createContext<AuthContextType | undefined>(undefined)

/**
 * AuthProvider wraps our entire app (in main.tsx) and manages
 * the single source of truth for authentication state.
 *
 * It listens to Supabase's onAuthStateChange event, which fires
 * automatically whenever:
 * - A user logs in
 * - A user logs out
 * - The session token refreshes in the background
 *
 * This means any component using useAuth() will automatically
 * re-render with fresh data when auth state changes anywhere
 * in the app - no manual refresh needed.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null)
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // On initial app load, check if there's an existing session
    // (e.g., user was already logged in from a previous visit)
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)
    })

    // Subscribe to all future auth state changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
      setUser(session?.user ?? null)
    })

    // Cleanup: unsubscribe when component unmounts to prevent memory leaks
    return () => subscription.unsubscribe()
  }, [])

  return (
    <AuthContext.Provider value={{ user, session, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

/**
 * Custom hook for accessing auth state from any component.
 * Usage: const { user, loading } = useAuth()
 */
export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}