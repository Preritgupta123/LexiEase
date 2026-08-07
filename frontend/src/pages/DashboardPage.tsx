import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { supabase } from '../lib/supabaseClient'

/**
 * DashboardPage - the main authenticated landing page.
 * This is a placeholder for now; document upload and history
 * will be added here in later steps.
 */
function DashboardPage() {
  const { user } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await supabase.auth.signOut()
    // onAuthStateChange (in AuthContext) will automatically
    // update the global user state to null after this.
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-2xl font-bold text-blue-600">
            LexiEase Dashboard
          </h1>
          <button
            onClick={handleLogout}
            className="text-sm text-gray-600 hover:text-red-600 border border-gray-300 rounded-md px-4 py-2 transition-colors"
          >
            Log Out
          </button>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <p className="text-gray-700">
            Welcome, <span className="font-semibold">{user?.email}</span>!
          </p>
          <p className="text-sm text-gray-500 mt-2">
            Document upload and analysis features coming soon.
          </p>
        </div>
      </div>
    </div>
  )
}

export default DashboardPage