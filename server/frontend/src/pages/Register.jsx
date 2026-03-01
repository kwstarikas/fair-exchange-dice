import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { isLoggedIn, storeTokens } from '../auth'

/**
 * Registration Page Component
 *
 * REACT CONCEPTS USED:
 * 1. useState - Stores form data that changes when user types
 * 2. Event handlers - Functions that run when user interacts (onClick, onChange)
 * 3. JSX - HTML-like syntax (the return statement)
 */
function Register() {
  // useState creates a "state variable"
  // formData = current value, setFormData = function to update it
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  })

  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  // Redirect if already logged in
  useEffect(() => {
    if (isLoggedIn()) {
      navigate('/dashboard')
    }
  }, [navigate])

  // This runs when any input changes
  // "e" is the event object, e.target is the input element
  const handleChange = (e) => {
    setFormData({
      ...formData,  // Keep existing data
      [e.target.name]: e.target.value  // Update the changed field
    })
    // Clear error when user starts typing
    if (error) setError('')
  }

  // Client-side validation
  const validateForm = () => {
    if (formData.username.length < 3) {
      setError('Username must be at least 3 characters')
      return false
    }
    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters')
      return false
    }
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match')
      return false
    }
    // Check for common weak passwords
    const weakPasswords = ['password', '12345678', 'qwerty123']
    if (weakPasswords.includes(formData.password.toLowerCase())) {
      setError('Password is too common. Choose a stronger password.')
      return false
    }
    return true
  }

  // This runs when form is submitted
  const handleSubmit = async (e) => {
    e.preventDefault()  // Prevent page reload
    setError('')

    // Validate before sending
    if (!validateForm()) return

    setLoading(true)

    try {
      // Send data to Django API
      const response = await fetch('/api/auth/register/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          first_name: formData.firstName,
          last_name: formData.lastName,
          username: formData.username,
          email: formData.email,
          password: formData.password
        })
      })

      const data = await response.json()

      if (response.ok) {
        storeTokens(data.tokens)
        navigate('/dashboard')
      } else {
        // Display the error message from the API
        setError(data.error || 'Registration failed. Please try again.')
      }
    } catch (err) {
      setError('Network error. Please check your connection and try again.')
    } finally {
      setLoading(false)
    }
  }

  // JSX - looks like HTML but it's JavaScript
  return (
    <div className="register-container">
      <h2>Create Account</h2>

      {/* Show error if exists */}
      {error && <div className="error">{error}</div>}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="firstName">First Name</label>
          <input
            type="text"
            id="firstName"
            name="firstName"
            value={formData.firstName}
            onChange={handleChange}
            required
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="lastName">Last Name</label>
          <input
            type="text"
            id="lastName"
            name="lastName"
            value={formData.lastName}
            onChange={handleChange}
            required
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="username">Username</label>
          <input
            type="text"
            id="username"
            name="username"
            value={formData.username}
            onChange={handleChange}
            required
            minLength={3}
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="email">Email</label>
          <input
            type="email"
            id="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            required
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            type="password"
            id="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            required
            minLength={8}
            disabled={loading}
          />
          <small className="hint">At least 8 characters, not a common word</small>
        </div>

        <div className="form-group">
          <label htmlFor="confirmPassword">Confirm Password</label>
          <input
            type="password"
            id="confirmPassword"
            name="confirmPassword"
            value={formData.confirmPassword}
            onChange={handleChange}
            required
            disabled={loading}
          />
        </div>

        <button type="submit" disabled={loading}>
          {loading ? 'Creating account...' : 'Register'}
        </button>
      </form>

      <p>Already have an account? <a href="/login">Login</a></p>
    </div>
  )
}

export default Register
