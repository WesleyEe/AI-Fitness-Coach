import { useEffect, useState } from 'react'
import Chat from './Chat'

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
    <main style={{ textAlign: 'center', maxWidth: 640, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
      <h1>Fitness Coach AI Assistant</h1>
      {error && <p style={{ color: 'crimson' }}>Backend unreachable: {error}</p>}
      {health && (
        <p style={{ fontSize: '0.85rem', opacity: 0.6 }}>
          API: {health.status} · DB connected: {String(health.db_connected)}
        </p>
      )}
      <Chat />
    </main>
  )
}

export default App
