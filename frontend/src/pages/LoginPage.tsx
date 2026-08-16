import { useState, type FormEvent } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { supabase } from '../lib/supabaseClient'

/**
 * LoginPage handles existing user authentication.
 *
 * On successful login, Supabase automatically fires the
 * onAuthStateChange event (see AuthContext.tsx), which updates
 * the global user state. We just need to redirect afterward.
 */
function LoginPage() {
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const handleLogin = async (e: FormEvent) => {
    e.preventDefault()
    setErrorMessage(null)
    setLoading(true)

    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })

    setLoading(false)

    if (error) {
      setErrorMessage(error.message)
      return
    }

    // Redirect to dashboard after successful login
    navigate('/dashboard')
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      {/* Card Container */}
      <div className="max-w-md w-full space-y-6">

        {/* Logo + Tagline */}
        <div className="text-center">
          <div className="flex items-center justify-center gap-2 mb-2">
            <span className="text-3xl">⚖️</span>
            <h1 className="text-3xl font-bold text-blue-600">LexiEase</h1>
          </div>
          <p className="text-gray-500 text-sm">
            Sign in to analyze your legal documents
          </p>
        </div>

        {/* Login Form Card */}
        <div className="bg-white rounded-xl shadow-md p-8">
          <h2 className="text-2xl font-bold text-gray-800 mb-6">
            Welcome back
          </h2>

          <form onSubmit={handleLogin} className="space-y-4">

            {/* Email Field */}
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Email address
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="you@example.com"
              />
            </div>

            {/* Password Field */}
            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Password
              </label>
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Your password"
              />
            </div>

            {/* Error Message */}
            {errorMessage && (
              <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-md p-2">
                {errorMessage}
              </p>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {loading ? 'Signing in...' : 'Sign In →'}
            </button>

          </form>

          {/* Sign Up Link */}
          <p className="text-center text-sm text-gray-600 mt-4">
            Don't have an account?{' '}
            <Link
              to="/signup"
              className="text-blue-600 font-medium hover:underline"
            >
              Sign up free
            </Link>
          </p>

          {/* Back to Home Link ✅ */}
          <p className="text-center text-sm text-gray-400 mt-2">
            <Link
              to="/"
              className="hover:text-gray-600 hover:underline transition-colors"
            >
              ← Back to home
            </Link>
          </p>

        </div>
      </div>
    </div>
  )
}

export default LoginPage