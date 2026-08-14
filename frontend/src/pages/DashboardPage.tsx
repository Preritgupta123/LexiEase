/**
 * DashboardPage.tsx - M9
 * Main dashboard for LexiEase.
 *
 * Features:
 * - Upload new documents
 * - View all uploaded documents
 * - Run pipeline (chunking + embedding)
 * - Run risk analysis
 * - Ask questions about documents (RAG)
 * - View analysis history
 */

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { supabase } from '../lib/supabaseClient'
import {
  getUserDocuments,
  processDocument,
  analyzeDocumentRisks,
  queryDocument,
  uploadDocument,
} from '../lib/api'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
interface Document {
  id: string
  file_name: string
  status: string
  created_at: string
  analyses_count: number
}

interface RiskFlag {
  risk_level: 'HIGH' | 'MEDIUM' | 'LOW'
  clause: string
  explanation: string
  recommendation: string
}

interface RiskResult {
  analysis_id: string
  total_risks: number
  high_count: number
  medium_count: number
  low_count: number
  risk_flags: RiskFlag[]
}

interface QueryResult {
  answer: string
  query: string
  source_chunks: { chunk_text: string; similarity: number }[]
}

// ---------------------------------------------------------------------------
// Risk badge color helper
// ---------------------------------------------------------------------------
function RiskBadge({ level }: { level: string }) {
  const colors: Record<string, string> = {
    HIGH: 'bg-red-100 text-red-700 border border-red-300',
    MEDIUM: 'bg-yellow-100 text-yellow-700 border border-yellow-300',
    LOW: 'bg-green-100 text-green-700 border border-green-300',
  }
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-bold ${colors[level] || ''}`}>
      {level}
    </span>
  )
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------
export default function DashboardPage() {
  const { user } = useAuth()
  const navigate = useNavigate()

  // State
  const [documents, setDocuments] = useState<Document[]>([])
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null)
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [processing, setProcessing] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [riskResult, setRiskResult] = useState<RiskResult | null>(null)
  const [query, setQuery] = useState('')
  const [querying, setQuerying] = useState(false)
  const [queryResult, setQueryResult] = useState<QueryResult | null>(null)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // ---------------------------------------------------------------------------
  // Load documents on mount
  // ---------------------------------------------------------------------------
  useEffect(() => {
    loadDocuments()
  }, [])

  async function loadDocuments() {
    setLoading(true)
    try {
      const data = await getUserDocuments()
      setDocuments(data.documents || [])
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------
  async function handleLogout() {
    await supabase.auth.signOut()
    navigate('/login')
  }

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return

    setUploading(true)
    setError('')
    setSuccess('')
    try {
      await uploadDocument(file)
      setSuccess('Document uploaded successfully!')
      await loadDocuments()
    } catch (err: any) {
      setError(err.message)
    } finally {
      setUploading(false)
    }
  }

  async function handleProcess(docId: string) {
    setProcessing(true)
    setError('')
    setSuccess('')
    try {
      const result = await processDocument(docId)
      setSuccess(`Pipeline complete! ${result.chunks_created} chunks created.`)
      await loadDocuments()
    } catch (err: any) {
      setError(err.message)
    } finally {
      setProcessing(false)
    }
  }

  async function handleAnalyze(docId: string) {
    setAnalyzing(true)
    setError('')
    setSuccess('')
    setRiskResult(null)
    try {
      const result = await analyzeDocumentRisks(docId)
      setRiskResult(result)
      setSuccess(`Analysis complete! Found ${result.total_risks} risks.`)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setAnalyzing(false)
    }
  }

  async function handleQuery() {
    if (!query.trim() || !selectedDoc) return
    setQuerying(true)
    setError('')
    setQueryResult(null)
    try {
      const result = await queryDocument(selectedDoc.id, query)
      setQueryResult(result)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setQuerying(false)
    }
  }

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-blue-600">⚖️ LexiEase</h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-500">{user?.email}</span>
            <button
              onClick={handleLogout}
              className="text-sm text-gray-600 hover:text-red-600 border border-gray-300 rounded-md px-4 py-2 transition-colors"
            >
              Log Out
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8 space-y-8">

        {/* Alerts */}
        {error && (
          <div className="bg-red-50 border border-red-300 text-red-700 px-4 py-3 rounded-lg">
            ❌ {error}
          </div>
        )}
        {success && (
          <div className="bg-green-50 border border-green-300 text-green-700 px-4 py-3 rounded-lg">
            ✅ {success}
          </div>
        )}

        {/* Upload Section */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">
            📄 Upload Legal Document
          </h2>
          <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-blue-300 rounded-lg cursor-pointer hover:bg-blue-50 transition-colors">
            <span className="text-blue-500 font-medium">
              {uploading ? 'Uploading...' : 'Click to upload PDF'}
            </span>
            <span className="text-gray-400 text-sm mt-1">PDF files only</span>
            <input
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={handleFileUpload}
              disabled={uploading}
            />
          </label>
        </div>

        {/* Documents List */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">
            📁 Your Documents
          </h2>

          {loading ? (
            <p className="text-gray-400">Loading documents...</p>
          ) : documents.length === 0 ? (
            <p className="text-gray-400">No documents yet. Upload one above!</p>
          ) : (
            <div className="space-y-3">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  onClick={() => {
                    setSelectedDoc(doc)
                    setRiskResult(null)
                    setQueryResult(null)
                    setError('')
                    setSuccess('')
                  }}
                  className={`p-4 rounded-lg border cursor-pointer transition-all ${
                    selectedDoc?.id === doc.id
                      ? 'border-blue-400 bg-blue-50'
                      : 'border-gray-200 hover:border-blue-300'
                  }`}
                >
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="font-medium text-gray-800">{doc.file_name}</p>
                      <p className="text-sm text-gray-400">
                        {new Date(doc.created_at).toLocaleDateString()} •{' '}
                        {doc.analyses_count} analyses
                      </p>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                      doc.status === 'uploaded'
                        ? 'bg-gray-100 text-gray-600'
                        : doc.status === 'extracted'
                        ? 'bg-blue-100 text-blue-600'
                        : 'bg-green-100 text-green-600'
                    }`}>
                      {doc.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Selected Document Actions */}
        {selectedDoc && (
          <div className="bg-white rounded-xl shadow-sm p-6 space-y-6">
            <h2 className="text-lg font-semibold text-gray-800">
              🔍 Analyzing: <span className="text-blue-600">{selectedDoc.file_name}</span>
            </h2>

            {/* Action Buttons */}
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => handleProcess(selectedDoc.id)}
                disabled={processing}
                className="bg-blue-600 text-white px-5 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {processing ? '⏳ Processing...' : '⚙️ Run Pipeline'}
              </button>

              <button
                onClick={() => handleAnalyze(selectedDoc.id)}
                disabled={analyzing}
                className="bg-red-600 text-white px-5 py-2 rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors"
              >
                {analyzing ? '⏳ Analyzing...' : '🔴 Analyze Risks'}
              </button>
            </div>

            {/* Risk Results */}
            {riskResult && (
              <div className="space-y-4">
                <div className="flex gap-4">
                  <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-center">
                    <p className="text-2xl font-bold text-red-600">{riskResult.high_count}</p>
                    <p className="text-xs text-red-500">HIGH</p>
                  </div>
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg px-4 py-3 text-center">
                    <p className="text-2xl font-bold text-yellow-600">{riskResult.medium_count}</p>
                    <p className="text-xs text-yellow-500">MEDIUM</p>
                  </div>
                  <div className="bg-green-50 border border-green-200 rounded-lg px-4 py-3 text-center">
                    <p className="text-2xl font-bold text-green-600">{riskResult.low_count}</p>
                    <p className="text-xs text-green-500">LOW</p>
                  </div>
                </div>

                <div className="space-y-3">
                  {riskResult.risk_flags.map((risk, i) => (
                    <div key={i} className="border border-gray-200 rounded-lg p-4 space-y-2">
                      <div className="flex items-center gap-2">
                        <RiskBadge level={risk.risk_level} />
                        <p className="font-medium text-gray-800 text-sm">{risk.clause}</p>
                      </div>
                      <p className="text-sm text-gray-600">⚠️ {risk.explanation}</p>
                      <p className="text-sm text-blue-600">💡 {risk.recommendation}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* RAG Query Section */}
            <div className="border-t pt-4 space-y-3">
              <h3 className="font-semibold text-gray-700">💬 Ask About This Document</h3>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleQuery()}
                  placeholder="e.g. What are my payment obligations?"
                  className="flex-1 border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                />
                <button
                  onClick={handleQuery}
                  disabled={querying || !query.trim()}
                  className="bg-green-600 text-white px-5 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
                >
                  {querying ? '⏳' : 'Ask'}
                </button>
              </div>

              {queryResult && (
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-2">
                  <p className="text-sm font-semibold text-gray-600">Answer:</p>
                  <p className="text-sm text-gray-800 whitespace-pre-wrap">{queryResult.answer}</p>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}