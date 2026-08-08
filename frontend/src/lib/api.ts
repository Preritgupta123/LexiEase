import { supabase } from './supabaseClient'

const API_BASE_URL = 'http://127.0.0.1:8000'

/**
 * Uploads a document file to our backend.
 *
 * Automatically attaches the current user's Supabase session
 * token as a Bearer token, so the backend can identify who's
 * uploading (matching our /documents/upload endpoint's
 * authentication requirement).
 */
export async function uploadDocument(file: File) {
  // Get the current session to extract the access token.
  const { data: sessionData } = await supabase.auth.getSession()
  const token = sessionData.session?.access_token

  if (!token) {
    throw new Error('You must be logged in to upload documents.')
  }

  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: 'POST',
    headers: {
      // Note: We do NOT set Content-Type here - the browser
      // automatically sets it correctly (including the required
      // multipart boundary) when using FormData.
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  })

  if (!response.ok) {
    const errorData = await response.json()
    throw new Error(errorData.detail || 'Upload failed.')
  }

  return response.json()
}