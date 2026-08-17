import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

interface ProtectedRouteProps {
  children: ReactNode
}

/**
 * ProtectedRoute wraps any page that requires authentication.
 *
 * Usage:
 *   <Route path="/dashboard" element={
 *     <ProtectedRoute><DashboardPage /></ProtectedRoute>
 *   } />
 *
 * Behavior:
 * - While auth state is still loading (initial page load), show nothing
 *   briefly rather than flashing a redirect prematurely.
 * - If no user is logged in, redirect to /login.
 * - Otherwise, render the protected page normally.
 */
function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { user, loading } = useAuth()

  if (loading) {
    // Avoid a flash of redirect while we're still checking
    // the initial session on page load/refresh.
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">Loading...</p>
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/LandingPage" replace />
  }

  return <>{children}</>
}

export default ProtectedRoute