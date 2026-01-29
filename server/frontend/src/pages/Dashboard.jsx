import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

/**
 * Dashboard Page - Shows after login
 * 
 * REACT CONCEPTS:
 * - useEffect: Runs code when component loads (like fetching user data)
 * - useNavigate: Programmatic navigation (redirect)
 * - Conditional rendering: Show different UI based on state
 */
function Dashboard() {
  const [user, setUser] = useState(null)
  const [diceValue, setDiceValue] = useState(1)
  const [rolling, setRolling] = useState(false)
  const navigate = useNavigate()

  // Check if user is logged in when component loads
  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      navigate('/login')
      return
    }

    // Fetch user info
    fetchUser(token)
  }, [navigate])

  const fetchUser = async (token) => {
    try {
      const response = await fetch('/api/auth/me/', {
        headers: {
          'Authorization': `Token ${token}`
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        setUser(data)
      } else {
        // Token invalid, redirect to login
        localStorage.removeItem('token')
        navigate('/login')
      }
    } catch (err) {
      console.error('Failed to fetch user:', err)
    }
  }

  const rollDice = () => {
    setRolling(true)
    
    // Animate dice rolling
    let rolls = 0
    const interval = setInterval(() => {
      setDiceValue(Math.floor(Math.random() * 6) + 1)
      rolls++
      
      if (rolls > 10) {
        clearInterval(interval)
        setDiceValue(Math.floor(Math.random() * 6) + 1)
        setRolling(false)
      }
    }, 100)
  }

  const handleLogout = async () => {
    const token = localStorage.getItem('token')
    
    try {
      await fetch('/api/auth/logout/', {
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`
        }
      })
    } catch (err) {
      console.error('Logout error:', err)
    }
    
    localStorage.removeItem('token')
    navigate('/')
  }

  // Dice face representations
  const diceFaces = {
    1: '⚀',
    2: '⚁',
    3: '⚂',
    4: '⚃',
    5: '⚄',
    6: '⚅'
  }

  if (!user) {
    return (
      <div className="dashboard-container">
        <p>Loading...</p>
      </div>
    )
  }

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>Welcome, {user.username}!</h1>
        <button onClick={handleLogout} className="logout-btn">Logout</button>
      </header>

      <div className="dice-section">
        <div className={`dice ${rolling ? 'rolling' : ''}`}>
          {diceFaces[diceValue]}
        </div>
        
        <button 
          onClick={rollDice} 
          disabled={rolling}
          className="roll-btn"
        >
          {rolling ? 'Rolling...' : 'Roll Dice'}
        </button>
        
        <p className="dice-result">
          You rolled: <strong>{diceValue}</strong>
        </p>
      </div>

      <div className="user-info">
        <h3>Your Profile</h3>
        <p><strong>Username:</strong> {user.username}</p>
        <p><strong>Email:</strong> {user.email || 'Not set'}</p>
        <p><strong>Joined:</strong> {new Date(user.date_joined).toLocaleDateString()}</p>
      </div>
    </div>
  )
}

export default Dashboard
