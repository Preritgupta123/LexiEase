import { Routes, Route, Navigate } from 'react-router-dom'
import SignupPage from './pages/SignupPage'

/**
 * Root App component - defines all application routes.
 * More routes (login, dashboard, etc.) will be added
 * in upcoming steps.
 */
function App() {
  return (
    <Routes>
      <Route path="/signup" element={<SignupPage />} />

      {/* Temporary: redirect root path to signup until
          we build the login page and a proper landing page */}
      <Route path="/" element={<Navigate to="/signup" replace />} />
    </Routes>
  )
}

export default App