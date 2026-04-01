// Tokens are stored in httpOnly cookies set by the server.
// JS cannot read httpOnly cookies, so a non-httpOnly "logged_in" flag cookie
// is used to detect login state without exposing the actual tokens.

const LOGGED_IN_COOKIE = 'logged_in'

function _getCookie(name) {
  const match = document.cookie.match(
    new RegExp('(?:^|; )' + name.replace(/([.$?*|{}()[\]\\/+^])/g, '\\$1') + '=([^;]*)')
  )
  return match ? decodeURIComponent(match[1]) : null
}

export function isLoggedIn() {
  return _getCookie(LOGGED_IN_COOKIE) === 'true'
}

export function clearTokens() {
  // httpOnly cookies (access_token, refresh_token) can only be cleared by the server.
  // We clear only the JS-readable flag cookie here.
  document.cookie = `${LOGGED_IN_COOKIE}=; max-age=0; path=/`
}

// ── Singleton token refresh ────────────────────────────────────────────────────
// Ensures only one refresh request is in flight at a time, preventing the race
// condition where two simultaneous 401s each try to use the same refresh token.

let _refreshPromise = null

async function _executeRefresh() {
  const res = await fetch('/api/auth/token/refresh/', {
    method: 'POST',
    credentials: 'include',  // send httpOnly cookies
  })

  if (res.ok) {
    // Server sets new cookies; nothing for JS to store
    return true
  } else if (res.status === 429) {
    // Rate limited — cookies still valid, don't clear
    return false
  } else {
    // 401/400 — refresh token invalid or expired
    clearTokens()
    return false
  }
}

function refreshOnce() {
  if (!_refreshPromise) {
    _refreshPromise = _executeRefresh().finally(() => {
      _refreshPromise = null
    })
  }
  return _refreshPromise
}

// ── Authenticated fetch wrapper ────────────────────────────────────────────────

export async function authFetch(url, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
    // No Authorization header — browser sends httpOnly cookies automatically
  }

  let response = await fetch(url, { ...options, headers, credentials: 'include' })

  if (response.status === 401) {
    const refreshed = await refreshOnce()
    if (refreshed) {
      response = await fetch(url, { ...options, headers, credentials: 'include' })
    }
  }

  return response
}
