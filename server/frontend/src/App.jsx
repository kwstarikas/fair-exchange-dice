import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import Register from './pages/Register'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import './App.css'

/**
 * Main App Component
 * 
 * REACT ROUTER CONCEPTS:
 * - BrowserRouter: Enables routing in your app
 * - Routes: Container for all routes
 * - Route: Maps a URL path to a component
 *   - path="/" means homepage
 *   - element={<Home />} means render the Home component
 */
function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/register" element={<Register />} />
          <Route path="/login" element={<Login />} />
          <Route path="/dashboard" element={<Dashboard />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

export default App
