import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

interface ProtectedRouteProps {
  children: ReactNode
}

/**
 * ProtectedRoute - Guards routes that require authentication.
 *
 * If user is not logged in → redirect to Landing page
 * If auth is still loading → show loading spinner
 * If user is logged in → render the protected page
 */
function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { user, loading } = useAuth()

  // Show loading while checking auth state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">Loading...</p>
      </div>
    )
  }

  // ✅ Redirect to home (landing page) if not logged in
  if (!user) {
    return <Navigate to="/" replace />
  }

  // User is authenticated - render the protected page
  return <>{children}</>
}

export default ProtectedRoute