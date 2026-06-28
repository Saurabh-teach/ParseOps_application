import React, { useState } from 'react'
import Api from './api'

export default function App() {
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function ping() {
    setLoading(true)
    setError(null)
    try {
      const json = await Api.get('/ping')
      setStatus(JSON.stringify(json, null, 2))
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{padding:20,fontFamily:'Inter, system-ui, Arial, sans-serif'}}>
      <h1>ParseOps Frontend</h1>
      <p>Minimal Vite + React scaffold. Connects to backend at <code>/api</code>.</p>

      <button onClick={ping} disabled={loading} style={{marginTop:10}}>
        {loading ? 'Pinging…' : 'Ping backend'}
      </button>

      {status && <pre style={{marginTop:10, whiteSpace: 'pre-wrap'}}>{status}</pre>}
      {error && <div style={{color: 'crimson', marginTop:10}}>Error: {error}</div>}
    </div>
  )
}
