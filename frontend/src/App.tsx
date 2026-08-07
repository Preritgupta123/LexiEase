import { useEffect, useState } from 'react'
import { supabase } from './lib/supabaseClient'

function App() {
  const [connectionStatus, setConnectionStatus] = useState<string>('Checking...')

  useEffect(() => {
    // Simple test: try to get the current session (will be null if not logged in,
    // but confirms the Supabase client initialized correctly without errors)
    supabase.auth.getSession().then(({ error }) => {
      if (error) {
        setConnectionStatus(`Error: ${error.message}`)
      } else {
        setConnectionStatus('Supabase client connected successfully ✅')
      }
    })
  }, [])

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-blue-600">
          LexiEase
        </h1>
        <p className="mt-2 text-gray-600">
          AI-Powered Legal Document Simplifier
        </p>
        <p className="mt-4 text-sm text-green-600">
          {connectionStatus}
        </p>
      </div>
    </div>
  )
}

export default App