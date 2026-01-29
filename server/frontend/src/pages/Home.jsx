import { Link, useNavigate } from 'react-router-dom'
import { useEffect } from 'react'

/**
 * Home Page Component
 * 
 * REACT CONCEPTS:
 * - Link component from react-router-dom (like <a> but for SPA navigation)
 * - useEffect to check auth status on load
 */
function Home() {
  const navigate = useNavigate()

  // Redirect to dashboard if already logged in
  useEffect(() => {
    const token = localStorage.getItem('token')
    if (token) {
      navigate('/dashboard')
    }
  }, [navigate])

  return (
    <div className="home-container">
      <h1>Fair Exchange Dice</h1>
      <p>Welcome to the fair exchange dice application.</p>
      
      <div className="home-actions">
        <Link to="/register" className="btn">Create Account</Link>
        <Link to="/login" className="btn btn-secondary">Login</Link>
      </div>
    </div>
  )
}

export default Home
