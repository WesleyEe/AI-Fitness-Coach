import { useEffect, useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

function App() {
  const [health, setHealth] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((res) => res.json())
      .then(setHealth)
      .catch((err) => setError(err.message))
  }, [])

  return (
    <main style={{ textAlign: 'center', maxWidth: 480 }}>
      <h1>Fitness Coach AI Assistant</h1>
      <p>Sprint 1: foundation check</p>
      {error && <p style={{ color: 'crimson' }}>Backend unreachable: {error}</p>}
      {!error && !health && <p>Checking backend health…</p>}
      {health && (
        <ul style={{ listStyle: 'none', padding: 0 }}>
          <li>API status: {health.status}</li>
          <li>Database connected: {String(health.db_connected)}</li>
        </ul>
      )}
    </main>
  )
}

export default App
