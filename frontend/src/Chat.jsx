import { useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

function Chat() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [userId, setUserId] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState(null)

  async function sendMessage(event) {
    event.preventDefault()
    const text = input.trim()
    if (!text || sending) return

    // The client holds the full conversation and sends it every turn -
    // the backend has no session state between requests.
    const nextMessages = [...messages, { role: 'user', content: text }]
    setMessages(nextMessages)
    setInput('')
    setSending(true)
    setError(null)

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: nextMessages,
          // No auth yet (Sprint 5) - a user id you created via POST /users lets the
          // agent look up your workout/injury history when a question needs it.
          user_id: userId ? Number(userId) : null,
        }),
      })
      if (!response.ok) {
        throw new Error(`Backend returned ${response.status}`)
      }
      const data = await response.json()
      setMessages([...nextMessages, data.message])
    } catch (err) {
      setError(err.message)
    } finally {
      setSending(false)
    }
  }

  return (
    <section style={{ width: '100%', maxWidth: 600, textAlign: 'left' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
        <label style={{ fontSize: '0.85rem', opacity: 0.7 }}>
          User ID (optional - lets the coach use your workout/injury history):
        </label>
        <input
          type="number"
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
          placeholder="e.g. 1"
          style={{ width: 70, padding: '0.25rem' }}
        />
      </div>

      <div
        style={{
          border: '1px solid #ccc',
          borderRadius: 8,
          padding: '1rem',
          minHeight: 300,
          maxHeight: 500,
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.75rem',
        }}
      >
        {messages.length === 0 && (
          <p style={{ opacity: 0.6 }}>
            Ask your coach something, e.g. "I have a football match this weekend. What
            training should I do this week?"
          </p>
        )}
        {messages.map((m, i) => (
          <div key={i}>
            <strong>{m.role === 'user' ? 'You' : 'Coach'}:</strong>
            <p style={{ margin: '0.25rem 0 0', whiteSpace: 'pre-wrap' }}>{m.content}</p>
          </div>
        ))}
        {sending && <p style={{ opacity: 0.6 }}>Coach is thinking…</p>}
      </div>

      {error && <p style={{ color: 'crimson' }}>Error: {error}</p>}

      <form onSubmit={sendMessage} style={{ display: 'flex', gap: '0.5rem', marginTop: '0.75rem' }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask your coach..."
          disabled={sending}
          style={{ flex: 1, padding: '0.5rem' }}
        />
        <button type="submit" disabled={sending || !input.trim()}>
          Send
        </button>
      </form>
    </section>
  )
}

export default Chat
