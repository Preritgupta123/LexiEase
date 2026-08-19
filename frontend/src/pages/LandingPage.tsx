/**
 * LandingPage.tsx
 * Public landing page - first thing users see when visiting the site.
 */

import { Link } from 'react-router-dom'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">

      {/* Navbar */}
      <nav className="flex items-center justify-between px-8 py-4 bg-white shadow-sm">
        <div className="flex items-center gap-2">
          <span className="text-2xl">⚖️</span>
          <span className="text-xl font-bold text-blue-700">LexiEase</span>
        </div>
        <div className="flex items-center gap-4">
          <Link
            to="/login"
            className="text-gray-600 hover:text-blue-600 text-sm font-medium transition-colors"
          >
            Sign In
          </Link>
          <Link
            to="/signup"
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            Get Started Free
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="max-w-4xl mx-auto px-8 py-20 text-center">

        {/* Badge */}
        <div className="inline-flex items-center gap-2 bg-blue-50 border border-blue-200 text-blue-700 text-sm px-4 py-2 rounded-full mb-8">
          <span>⚡</span>
          <span>AI-Powered Legal Document Analysis</span>
        </div>

        {/* Heading */}
        <h1 className="text-5xl font-bold text-gray-900 mb-6 leading-tight">
          Understand Your{' '}
          <span className="text-blue-600">Legal Documents</span>{' '}
          Before You Sign
        </h1>

        {/* Subheading */}
        <p className="text-xl text-gray-600 mb-10 max-w-2xl mx-auto leading-relaxed">
          Upload any rent agreement or legal document. LexiEase uses AI to
          identify risky clauses, explain them in plain English, and help
          you make informed decisions.
        </p>

        {/* CTA Buttons */}
        <div className="flex items-center justify-center gap-4 mb-16">
          <Link
            to="/signup"
            className="bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors text-lg"
          >
            Analyze My Document →
          </Link>
          <Link
            to="/login"
            className="text-gray-600 border border-gray-300 px-8 py-3 rounded-lg font-semibold hover:border-blue-400 hover:text-blue-600 transition-colors text-lg"
          >
            Sign In
          </Link>
        </div>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left">

          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="text-3xl mb-3">📄</div>
            <h3 className="font-bold text-gray-800 mb-2">
              Upload Any PDF
            </h3>
            <p className="text-gray-500 text-sm">
              Works with both digital and scanned PDF documents including
              rent agreements and legal contracts.
            </p>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="text-3xl mb-3">🔍</div>
            <h3 className="font-bold text-gray-800 mb-2">
              AI Risk Analysis
            </h3>
            <p className="text-gray-500 text-sm">
              Automatically identifies HIGH, MEDIUM, and LOW risk clauses
              with plain English explanations.
            </p>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="text-3xl mb-3">💡</div>
            <h3 className="font-bold text-gray-800 mb-2">
              Actionable Advice
            </h3>
            <p className="text-gray-500 text-sm">
              Get specific recommendations on what to negotiate or change
              before signing any agreement.
            </p>
          </div>

        </div>
      </main>

      {/* Footer */}
      <footer className="text-center py-8 text-gray-400 text-sm">
        <p>© 2025 LexiEase. Built to protect your legal rights.</p>
      </footer>

    </div>
  )
}