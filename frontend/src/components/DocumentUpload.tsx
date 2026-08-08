import { useState, type ChangeEvent } from 'react'
import { uploadDocument } from '../lib/api'

/**
 * DocumentUpload provides a file picker and handles the
 * full upload flow: selecting a file, sending it to the backend,
 * and showing success/error feedback.
 */
function DocumentUpload() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    setSelectedFile(file || null)
    setErrorMessage(null)
    setSuccessMessage(null)
  }

  const handleUpload = async () => {
    if (!selectedFile) return

    setUploading(true)
    setErrorMessage(null)
    setSuccessMessage(null)

    try {
      const result = await uploadDocument(selectedFile)
      setSuccessMessage(
        `"${result.file_name}" uploaded successfully! Status: ${result.status}`
      )
      setSelectedFile(null)
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : 'Upload failed.'
      )
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-lg font-semibold text-gray-800 mb-4">
        Upload a Legal Document
      </h2>

      <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
        <input
          type="file"
          accept="application/pdf"
          onChange={handleFileChange}
          className="block w-full text-sm text-gray-600
                     file:mr-4 file:py-2 file:px-4
                     file:rounded-md file:border-0
                     file:bg-blue-50 file:text-blue-700
                     hover:file:bg-blue-100
                     file:cursor-pointer cursor-pointer"
        />
        <p className="text-xs text-gray-400 mt-2">
          PDF only, max 10MB
        </p>
      </div>

      {selectedFile && (
        <div className="mt-4 flex items-center justify-between bg-gray-50 rounded-md p-3">
          <span className="text-sm text-gray-700 truncate">
            {selectedFile.name}
          </span>
          <button
            onClick={handleUpload}
            disabled={uploading}
            className="ml-4 bg-blue-600 text-white text-sm py-1.5 px-4 rounded-md
                       hover:bg-blue-700 disabled:opacity-50
                       disabled:cursor-not-allowed transition-colors"
          >
            {uploading ? 'Uploading...' : 'Upload'}
          </button>
        </div>
      )}

      {errorMessage && (
        <p className="mt-4 text-sm text-red-600 bg-red-50 border border-red-200 rounded-md p-2">
          {errorMessage}
        </p>
      )}

      {successMessage && (
        <p className="mt-4 text-sm text-green-700 bg-green-50 border border-green-200 rounded-md p-2">
          {successMessage}
        </p>
      )}
    </div>
  )
}

export default DocumentUpload