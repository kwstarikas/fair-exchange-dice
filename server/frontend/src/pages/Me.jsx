import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { isLoggedIn, clearTokens, authFetch } from '../auth'

function Me() {
  const [user, setUser] = useState(null)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    if (!isLoggedIn()) { navigate('/login'); return }

    authFetch('/api/auth/me/')
      .then(res => {
        if (res.ok) return res.json()
        if (res.status === 401) { clearTokens(); navigate('/login') }
      })
      .then(data => { if (data) setUser(data) })
      .catch(() => {})
  }, [navigate])

  async function handleDeleteAccount() {
    setError('')
    try {
      await authFetch('/api/auth/delete_account/', { method: 'DELETE' })
    } catch {
      setError('Something went wrong. Please try again.')
      return
    }
    clearTokens()
    navigate('/')
  }

  if (!user) {
    return <div className="me-container"><p>Loading...</p></div>
  }

  return (
    <div className="me-container">
      <header className="me-header">
        <Link to="/dashboard" className="back-link">← Back to lobby</Link>
        <h1>My Account</h1>
      </header>

      <section className="me-section">
        <div className="me-row">
          <span className="me-label">Username</span>
          <span className="me-value">{user.username}</span>
        </div>
        <div className="me-row">
          <span className="me-label">Email</span>
          <span className="me-value">{user.email || '—'}</span>
        </div>
        <div className="me-row">
          <span className="me-label">First name</span>
          <span className="me-value">{user.first_name || '—'}</span>
        </div>
        <div className="me-row">
          <span className="me-label">Last name</span>
          <span className="me-value">{user.last_name || '—'}</span>
        </div>
        <div className="me-row">
          <span className="me-label">Member since</span>
          <span className="me-value">{new Date(user.date_joined).toLocaleDateString()}</span>
        </div>
      </section>

      <section className="me-danger-zone">
        <h2>Danger zone</h2>
        {error && <p className="error">{error}</p>}
        {!confirmDelete ? (
          <button className="delete-btn" onClick={() => setConfirmDelete(true)}>
            Delete account
          </button>
        ) : (
          <div className="delete-confirm">
            <p>This will permanently delete your account and all your game history. Are you sure?</p>
            <div className="delete-confirm-actions">
              <button className="delete-btn" onClick={handleDeleteAccount}>Yes, delete my account</button>
              <button className="cancel-btn" onClick={() => setConfirmDelete(false)}>Cancel</button>
            </div>
          </div>
        )}
      </section>
    </div>
  )
}

export default Me
