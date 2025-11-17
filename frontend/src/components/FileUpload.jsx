import { useState } from 'react'
import { uploadActivityFile, getVideoStatus, getVideoUrl } from '../lib/api'
import { supabase } from '../lib/supabase'

export default function FileUpload() {
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [videoId, setVideoId] = useState(null)
  const [videoUrl, setVideoUrl] = useState(null)
  const [error, setError] = useState(null)
  const [dragActive, setDragActive] = useState(false)

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0])
    }
  }

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
    }
  }

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file')
      return
    }

    const allowedTypes = ['.gpx', '.tcx', '.fit']
    const fileExt = file.name.substring(file.name.lastIndexOf('.')).toLowerCase()

    if (!allowedTypes.includes(fileExt)) {
      setError('Please upload a GPX, TCX, or FIT file')
      return
    }

    try {
      setUploading(true)
      setError(null)
      setVideoUrl(null)

      const response = await uploadActivityFile(file)
      setVideoId(response.video_id)

      // If video is completed immediately, set the URL
      if (response.status === 'completed' && response.video_url) {
        const url = getVideoUrl(response.video_id)
        setVideoUrl(url)
      }

      setFile(null)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to upload file')
    } finally {
      setUploading(false)
    }
  }

  const handleSignOut = async () => {
    await supabase.auth.signOut()
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>Activity Video Generator</h1>
        <button onClick={handleSignOut} style={styles.signOutButton}>
          Sign Out
        </button>
      </div>

      <div style={styles.uploadSection}>
        <div
          style={{
            ...styles.dropZone,
            ...(dragActive ? styles.dropZoneActive : {}),
          }}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            type="file"
            id="file-upload"
            accept=".gpx,.tcx,.fit"
            onChange={handleFileChange}
            style={styles.fileInput}
          />
          <label htmlFor="file-upload" style={styles.uploadLabel}>
            {file ? (
              <div>
                <p style={styles.fileName}>{file.name}</p>
                <p style={styles.fileSize}>
                  {(file.size / 1024).toFixed(2)} KB
                </p>
              </div>
            ) : (
              <div>
                <p style={styles.uploadText}>
                  Drag and drop your activity file here
                </p>
                <p style={styles.uploadSubtext}>or click to browse</p>
                <p style={styles.uploadFormats}>Supported: GPX, TCX, FIT</p>
              </div>
            )}
          </label>
        </div>

        {error && <div style={styles.error}>{error}</div>}

        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          style={{
            ...styles.uploadButton,
            ...((!file || uploading) ? styles.uploadButtonDisabled : {}),
          }}
        >
          {uploading ? 'Generating Video...' : 'Generate Video'}
        </button>
      </div>

      {videoUrl && (
        <div style={styles.videoSection}>
          <h2 style={styles.videoTitle}>Generated Video</h2>
          <video
            controls
            style={styles.video}
            src={videoUrl}
            type="video/mp4"
          >
            Your browser does not support the video tag.
          </video>
          <a
            href={videoUrl}
            download={`activity_${videoId}.mp4`}
            style={styles.downloadButton}
          >
            Download Video
          </a>
        </div>
      )}
    </div>
  )
}

const styles = {
  container: {
    minHeight: '100vh',
    backgroundColor: '#f5f5f5',
    padding: '2rem',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '2rem',
    maxWidth: '800px',
    margin: '0 auto 2rem',
  },
  title: {
    fontSize: '28px',
    fontWeight: 'bold',
  },
  signOutButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#f44336',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
  },
  uploadSection: {
    maxWidth: '800px',
    margin: '0 auto',
    backgroundColor: 'white',
    padding: '2rem',
    borderRadius: '8px',
    boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
  },
  dropZone: {
    border: '2px dashed #ccc',
    borderRadius: '8px',
    padding: '3rem 2rem',
    textAlign: 'center',
    cursor: 'pointer',
    transition: 'all 0.3s',
  },
  dropZoneActive: {
    borderColor: '#4CAF50',
    backgroundColor: '#f0f8f0',
  },
  fileInput: {
    display: 'none',
  },
  uploadLabel: {
    cursor: 'pointer',
  },
  fileName: {
    fontSize: '18px',
    fontWeight: 'bold',
    marginBottom: '0.5rem',
  },
  fileSize: {
    color: '#666',
    fontSize: '14px',
  },
  uploadText: {
    fontSize: '18px',
    marginBottom: '0.5rem',
  },
  uploadSubtext: {
    color: '#666',
    marginBottom: '1rem',
  },
  uploadFormats: {
    fontSize: '14px',
    color: '#888',
  },
  error: {
    marginTop: '1rem',
    padding: '0.75rem',
    backgroundColor: '#ffebee',
    color: '#c62828',
    borderRadius: '4px',
  },
  uploadButton: {
    marginTop: '1rem',
    width: '100%',
    padding: '1rem',
    backgroundColor: '#4CAF50',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '16px',
    fontWeight: 'bold',
    cursor: 'pointer',
  },
  uploadButtonDisabled: {
    backgroundColor: '#ccc',
    cursor: 'not-allowed',
  },
  videoSection: {
    maxWidth: '800px',
    margin: '2rem auto',
    backgroundColor: 'white',
    padding: '2rem',
    borderRadius: '8px',
    boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
  },
  videoTitle: {
    fontSize: '20px',
    fontWeight: 'bold',
    marginBottom: '1rem',
  },
  video: {
    width: '100%',
    borderRadius: '4px',
    marginBottom: '1rem',
  },
  downloadButton: {
    display: 'inline-block',
    padding: '0.75rem 1.5rem',
    backgroundColor: '#2196F3',
    color: 'white',
    textDecoration: 'none',
    borderRadius: '4px',
    fontSize: '14px',
    fontWeight: 'bold',
  },
}
