/**
 * API Client - lib/api.ts
 * Central place for all backend API calls.
 * Automatically attaches the current user's Supabase session token.
 * Includes retry logic for Render free tier cold starts.
 */

import { supabase } from './supabaseClient'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

// ---------------------------------------------------------------------------
// Config: Retry settings for Render free tier cold start
// ---------------------------------------------------------------------------
const MAX_RETRIES = 3        // Try 3 times total
const RETRY_DELAY_MS = 3000  // Wait 3 seconds between retries

// ---------------------------------------------------------------------------
// Helper: Wait for X milliseconds
// ---------------------------------------------------------------------------
function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

// ---------------------------------------------------------------------------
// Helper: Get auth token from Supabase session
// ---------------------------------------------------------------------------
async function getAuthToken(): Promise<string> {
  const { data: sessionData } = await supabase.auth.getSession()
  const token = sessionData.session?.access_token
  if (!token) throw new Error('You must be logged in.')
  return token
}

// ---------------------------------------------------------------------------
// Helper: Authenticated fetch WITH retry logic
// Render free tier sleeps after 15min inactivity.
// First request after sleep takes 30-50 seconds → we retry automatically.
// ---------------------------------------------------------------------------
async function authFetch(endpoint: string, options: RequestInit = {}) {
  const token = await getAuthToken()

  let lastError: Error = new Error('Request failed.')

  for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
          ...options.headers,
        },
      })

      if (!response.ok) {
        const errorData = await response.json()
        // Don't retry on 4xx errors (bad request, unauthorized, etc.)
        // Only retry on 5xx (server errors) or network issues
        if (response.status < 500) {
          throw new Error(errorData.detail || 'Request failed.')
        }
        lastError = new Error(errorData.detail || 'Server error.')
        throw lastError
      }

      return response.json()

    } catch (error) {
      lastError = error as Error

      // If it's a 4xx client error, don't retry - throw immediately
      if (lastError.message && !lastError.message.includes('fetch')) {
        const msg = lastError.message
        if (!msg.includes('Server error') && !msg.includes('Failed to fetch')) {
          throw lastError
        }
      }

      // If we have retries left, wait and try again
      if (attempt < MAX_RETRIES) {
        console.warn(
          `API call failed (attempt ${attempt}/${MAX_RETRIES}). ` +
          `Backend may be waking up. Retrying in ${RETRY_DELAY_MS / 1000}s...`
        )
        await sleep(RETRY_DELAY_MS)
      }
    }
  }

  // All retries exhausted
  throw new Error(
    'Backend is starting up, please wait a moment and refresh the page.'
  )
}

// ---------------------------------------------------------------------------
// Documents
// ---------------------------------------------------------------------------

/** Upload a PDF document to the backend */
export async function uploadDocument(file: File) {
  const token = await getAuthToken()
  const formData = new FormData()
  formData.append('file', file)

  let lastError: Error = new Error('Upload failed.')

  // Retry upload too (cold start can affect first upload)
  for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    try {
      const response = await fetch(`${API_BASE_URL}/documents/upload`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        // Don't retry 4xx errors
        if (response.status < 500) {
          throw new Error(errorData.detail || 'Upload failed.')
        }
        lastError = new Error(errorData.detail || 'Upload server error.')
        continue
      }

      return response.json()

    } catch (error) {
      lastError = error as Error

      if (attempt < MAX_RETRIES) {
        console.warn(`Upload attempt ${attempt} failed. Retrying...`)
        await sleep(RETRY_DELAY_MS)
      }
    }
  }

  throw lastError
}

// ---------------------------------------------------------------------------
// Pipeline
// ---------------------------------------------------------------------------

/** Run chunking + embedding pipeline for a document */
export async function processDocument(documentId: string) {
  return authFetch(`/pipeline/process/${documentId}`, {
    method: 'POST',
  })
}

// ---------------------------------------------------------------------------
// RAG - Query
// ---------------------------------------------------------------------------

/** Ask a question about a legal document */
export async function queryDocument(
  documentId: string,
  query: string,
  matchCount: number = 5
) {
  return authFetch('/rag/query', {
    method: 'POST',
    body: JSON.stringify({
      document_id: documentId,
      query,
      match_count: matchCount,
    }),
  })
}

// ---------------------------------------------------------------------------
// Risk Analysis
// ---------------------------------------------------------------------------

/** Analyze a document for risky clauses */
export async function analyzeDocumentRisks(documentId: string) {
  return authFetch(`/risk/analyze/${documentId}`, {
    method: 'POST',
  })
}

/** Get all previous analyses for a document */
export async function getDocumentAnalyses(documentId: string) {
  return authFetch(`/risk/analyses/${documentId}`)
}

// ---------------------------------------------------------------------------
// History
// ---------------------------------------------------------------------------

/** Get all documents uploaded by the current user */
export async function getUserDocuments() {
  return authFetch('/history/documents')
}

/** Get a single document with all its analyses */
export async function getDocumentDetail(documentId: string) {
  return authFetch(`/history/documents/${documentId}`)
}

/** Delete a document and all its associated data */
export async function deleteDocument(documentId: string) {
  return authFetch(`/documents/${documentId}`, {
    method: 'DELETE',
  })
}