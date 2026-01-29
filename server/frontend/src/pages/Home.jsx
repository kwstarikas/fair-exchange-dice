import { Link } from 'react-router-dom'

/**
 * Home Page Component
 * 
 * REACT CONCEPTS:
 * - Link component from react-router-dom (like <a> but for SPA navigation)
 * - No state needed here - it's a "stateless" component
 */
function Home() {
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
