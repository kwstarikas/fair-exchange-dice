import { useState, useEffect, useRef } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { isLoggedIn, clearTokens, getRefreshToken, authFetch } from '../auth'

const diceFaces = { 1: '⚀', 2: '⚁', 3: '⚂', 4: '⚃', 5: '⚄', 6: '⚅' }

async function sha256hex(str) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(str))
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join('')
}

function generateNonce() {
  const arr = new Uint8Array(32)
  crypto.getRandomValues(arr)
  return Array.from(arr).map(b => b.toString(16).padStart(2, '0')).join('')
}

function Dashboard() {
  const [user, setUser] = useState(null)
  const [onlineUsers, setOnlineUsers] = useState([])
  const [games, setGames] = useState([])
  const [activeGameId, setActiveGameId] = useState(null)

  // Refs don't trigger re-renders — used for protocol state
  const pendingReveal = useRef({})  // { [gameId]: { nonce, value } }
  const revealSent = useRef({})     // { [gameId]: true }
  const userLoaded = useRef(false)

  const navigate = useNavigate()
  const fetchFailures = useRef(0)

  const activeGame = games.find(g => g.id === activeGameId) ?? null

  useEffect(() => {
    if (!isLoggedIn()) { navigate('/login'); return }

    let mounted = true

    async function fetchUser() {
      try {
        const res = await authFetch('/api/auth/me/')
        if (!mounted) return
        if (res.ok) {
          fetchFailures.current = 0
          userLoaded.current = true
          setUser(await res.json())
        } else if (res.status === 401) {
          clearTokens()
          navigate('/login')
        } else if (res.status === 429) {
          // Rate limited — temporary, don't count toward logout
        } else {
          // 5xx or other — count failures and give up after 5 tries
          fetchFailures.current++
          if (fetchFailures.current >= 5) {
            clearTokens()
            navigate('/login')
          }
        }
      } catch {
        fetchFailures.current++
        if (fetchFailures.current >= 5) {
          clearTokens()
          navigate('/login')
        }
      }
    }

    async function poll() {
      if (!mounted) return
      let usersRes, gamesRes
      try {
        ;[usersRes, gamesRes] = await Promise.all([
          authFetch('/api/game/online-users/'),
          authFetch('/api/game/'),
        ])
      } catch {
        return // network error — skip this tick
      }
      if (!mounted) return

      if (usersRes.ok) setOnlineUsers(await usersRes.json())

      // Retry user fetch if a transient error prevented it on first load
      if (!userLoaded.current) fetchUser()

      if (gamesRes.ok) {
        const updated = await gamesRes.json()
        setGames(updated)

        // Auto-reveal: when both players have committed, send our nonce+value
        for (const game of updated) {
          if (game.state === 'revealing' && !revealSent.current[game.id]) {
            const stored = pendingReveal.current[game.id]
            if (stored) {
              revealSent.current[game.id] = true
              const res = await authFetch(`/api/game/${game.id}/reveal/`, {
                method: 'POST',
                body: JSON.stringify({ nonce: stored.nonce, value: stored.value }),
              })
              if (res.ok && mounted) {
                const finished = await res.json()
                setGames(prev => prev.map(g => g.id === finished.id ? finished : g))
              }
            }
          }
        }
      }
    }

    fetchUser()
    authFetch('/api/game/heartbeat/', { method: 'POST' })
    poll()

    const heartbeatInterval = setInterval(
      () => authFetch('/api/game/heartbeat/', { method: 'POST' }),
      15000
    )
    const pollInterval = setInterval(poll, 5000)

    return () => {
      mounted = false
      clearInterval(heartbeatInterval)
      clearInterval(pollInterval)
    }
  }, [navigate])

  async function challengeUser(opponentId) {
    const res = await authFetch('/api/game/', {
      method: 'POST',
      body: JSON.stringify({ opponent_id: opponentId }),
    })
    if (res.ok) {
      const game = await res.json()
      setGames(prev => [game, ...prev.filter(g => g.id !== game.id)])
      setActiveGameId(game.id)
    }
  }

  async function acceptChallenge(gameId) {
    const res = await authFetch(`/api/game/${gameId}/accept/`, { method: 'POST' })
    if (res.ok) {
      const game = await res.json()
      setGames(prev => prev.map(g => g.id === game.id ? game : g))
      setActiveGameId(game.id)
    }
  }

  async function declineChallenge(gameId) {
    const res = await authFetch(`/api/game/${gameId}/decline/`, { method: 'POST' })
    if (res.ok) setGames(prev => prev.filter(g => g.id !== gameId))
  }

  async function rollDice(game) {
    const nonce = generateNonce()
    const value = Math.floor(Math.random() * 6) + 1
    const commitment = await sha256hex(`${nonce}${value}`)

    const res = await authFetch(`/api/game/${game.id}/commit/`, {
      method: 'POST',
      body: JSON.stringify({ commitment }),
    })
    if (res.ok) {
      // Store locally — only revealed after the opponent commits too
      pendingReveal.current[game.id] = { nonce, value }
      const updated = await res.json()
      setGames(prev => prev.map(g => g.id === updated.id ? updated : g))
    }
  }

  async function handleLogout() {
    try {
      await authFetch('/api/auth/logout/', {
        method: 'POST',
        body: JSON.stringify({ refresh: getRefreshToken() }),
      })
    } catch {}
    clearTokens()
    navigate('/')
  }


  if (!user) {
    return <div className="dashboard-container"><p>Loading...</p></div>
  }

  const userId = user.id
  const incoming = games.filter(g => g.state === 'pending' && g.opponent === userId)
  const outgoing = games.filter(g => g.state === 'pending' && g.challenger === userId)
  const active = games.filter(g => ['committing', 'revealing'].includes(g.state))
  const finished = games.filter(g => g.state === 'finished').slice(0, 5)

  function renderGame(game) {
    const isChallenger = game.challenger === userId
    const opponentName = isChallenger ? game.opponent_username : game.challenger_username
    const myCommit = isChallenger ? game.challenger_commit : game.opponent_commit
    const myValue = isChallenger ? game.challenger_value : game.opponent_value
    const oppValue = isChallenger ? game.opponent_value : game.challenger_value
    const stored = pendingReveal.current[game.id]

    return (
      <div className="game-view">
        <button onClick={() => setActiveGameId(null)} className="back-btn">← Back to lobby</button>
        <h2 className="game-title">vs {opponentName}</h2>

        {game.state === 'pending' && (
          <div className="game-phase">
            {isChallenger
              ? <p className="status-text">Waiting for {opponentName} to accept your challenge…</p>
              : (
                <div>
                  <p className="status-text">{opponentName} challenged you to a dice duel!</p>
                  <div className="game-actions">
                    <button onClick={() => acceptChallenge(game.id)} className="accept-btn">Accept</button>
                    <button onClick={() => declineChallenge(game.id)} className="decline-btn">Decline</button>
                  </div>
                </div>
              )
            }
          </div>
        )}

        {game.state === 'committing' && (
          <div className="game-phase">
            {!myCommit ? (
              <div>
                <p className="status-text">
                  Roll your dice. Your value is hidden from {opponentName} until both of you have rolled.
                </p>
                <button onClick={() => rollDice(game)} className="roll-btn">Roll Dice</button>
              </div>
            ) : (
              <div>
                <div className="dice-preview">{diceFaces[stored?.value]}</div>
                <p className="status-text">Rolled! Waiting for {opponentName}…</p>
                <p className="commit-hint">Your commitment: {myCommit.slice(0, 20)}…</p>
              </div>
            )}
          </div>
        )}

        {game.state === 'revealing' && (
          <div className="game-phase">
            {stored && (
              <div className="dice-preview">{diceFaces[stored.value]}</div>
            )}
            <p className="status-text">Both players rolled — verifying commitments…</p>
          </div>
        )}

        {game.state === 'finished' && (
          <div className="game-phase">
            <div className="dice-battle">
              <div className="player-dice">
                <p className="player-label">You</p>
                <span className="big-dice">{diceFaces[myValue]}</span>
                <p className="dice-number">{myValue}</p>
              </div>
              <span className="vs-text">VS</span>
              <div className="player-dice">
                <p className="player-label">{opponentName}</p>
                <span className="big-dice">{diceFaces[oppValue]}</span>
                <p className="dice-number">{oppValue}</p>
              </div>
            </div>
            {game.is_draw
              ? <p className="result-banner draw">Draw!</p>
              : game.winner === userId
                ? <p className="result-banner win">You Win!</p>
                : <p className="result-banner loss">You Lose</p>
            }
            <button onClick={() => setActiveGameId(null)} className="roll-btn back-to-lobby">
              Back to Lobby
            </button>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="dashboard-container wide">
      <header className="dashboard-header">
        <h1>Fair Exchange Dice</h1>
        <div className="header-right">
          <Link to="/me" className="username-badge">{user.username}</Link>
          <button onClick={handleLogout} className="logout-btn">Logout</button>
        </div>
      </header>

      {activeGame ? renderGame(activeGame) : (
        <div className="lobby">
          {incoming.length > 0 && (
            <section className="lobby-section">
              <h3>Incoming Challenges</h3>
              {incoming.map(g => (
                <div key={g.id} className="game-row">
                  <span><strong>{g.challenger_username}</strong> challenges you!</span>
                  <div className="row-actions">
                    <button onClick={() => acceptChallenge(g.id)} className="accept-btn">Accept</button>
                    <button onClick={() => declineChallenge(g.id)} className="decline-btn">Decline</button>
                  </div>
                </div>
              ))}
            </section>
          )}

          {active.length > 0 && (
            <section className="lobby-section">
              <h3>Active Games</h3>
              {active.map(g => {
                const oppName = g.challenger === userId ? g.opponent_username : g.challenger_username
                return (
                  <div key={g.id} className="game-row clickable" onClick={() => setActiveGameId(g.id)}>
                    <span>vs <strong>{oppName}</strong></span>
                    <span className={`state-badge ${g.state}`}>{g.state}</span>
                  </div>
                )
              })}
            </section>
          )}

          {outgoing.length > 0 && (
            <section className="lobby-section">
              <h3>Sent Challenges</h3>
              {outgoing.map(g => (
                <div key={g.id} className="game-row">
                  <span>Waiting for <strong>{g.opponent_username}</strong>…</span>
                </div>
              ))}
            </section>
          )}

          <section className="lobby-section">
            <h3>Online Players {onlineUsers.length > 0 && `(${onlineUsers.length})`}</h3>
            {onlineUsers.length === 0
              ? <p className="empty-text">No other players online right now</p>
              : onlineUsers.map(u => {
                const busy = [...active, ...incoming, ...outgoing].some(
                  g => g.challenger === u.id || g.opponent === u.id
                )
                return (
                  <div key={u.id} className="game-row">
                    <span>{u.username}</span>
                    <button
                      onClick={() => challengeUser(u.id)}
                      disabled={busy}
                      className="challenge-btn"
                    >
                      Challenge
                    </button>
                  </div>
                )
              })
            }
          </section>

          {finished.length > 0 && (
            <section className="lobby-section">
              <h3>Recent Games</h3>
              {finished.map(g => {
                const oppName = g.challenger === userId ? g.opponent_username : g.challenger_username
                const cls = g.is_draw ? 'draw' : g.winner === userId ? 'win' : 'loss'
                const label = g.is_draw ? 'Draw' : g.winner === userId ? 'Win' : 'Loss'
                return (
                  <div key={g.id} className="game-row clickable" onClick={() => setActiveGameId(g.id)}>
                    <span>vs <strong>{oppName}</strong></span>
                    <span className={`result-badge ${cls}`}>{label}</span>
                  </div>
                )
              })}
            </section>
          )}
        </div>
      )}
    </div>
  )
}

export default Dashboard
