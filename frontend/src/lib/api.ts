/**
 * API Client - lib/api.ts
 * Central place for all backend API calls.
 * Automatically attaches the current user's Supabase session token.
 */

import { supabase } from './supabaseClient'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

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
// Helper: Authenticated fetch wrapper
// ---------------------------------------------------------------------------
async function authFetch(endpoint: string, options: RequestInit = {}) {
  const token = await getAuthToken()
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
    throw new Error(errorData.detail || 'Request failed.')
  }
  return response.json()
}

// ---------------------------------------------------------------------------
// Documents
// ---------------------------------------------------------------------------

/** Upload a PDF document to the backend */
export async function uploadDocument(file: File) {
  const token = await getAuthToken()
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  })

  if (!response.ok) {
    const errorData = await response.json()
    throw new Error(errorData.detail || 'Upload failed.')
  }
  return response.json()
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