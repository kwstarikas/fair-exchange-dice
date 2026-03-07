const ACCESS_KEY = 'access_token'
const REFRESH_KEY = 'refresh_token'

export function storeTokens({ access, refresh }) {
  localStorage.setItem(ACCESS_KEY, access)
  localStorage.setItem(REFRESH_KEY, refresh)
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
}

export function getAccessToken() {
  return localStorage.getItem(ACCESS_KEY)
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_KEY)
}

export function isLoggedIn() {
  return !!localStorage.getItem(ACCESS_KEY)
}

/**
 * Singleton refresh — if a refresh is already in flight, all callers
 * await the same promise instead of each firing their own request.
 * This prevents the race condition where two simultaneous 401s both try
 * to use the same refresh token, causing the second to hit a blacklisted
 * token and wipe localStorage.
 */
let _refreshPromise = null

async function _executeRefresh() {
  const res = await fetch('/api/auth/token/refresh/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh: getRefreshToken() }),
  })

  if (res.ok) {
    const data = await res.json()
    if (!data.access) {
      clearTokens()
      return null
    }
    storeTokens({
      access: data.access,
      refresh: data.refresh ?? getRefreshToken(),
    })
    return data.access
  } else if (res.status === 429) {
    // Rate limited — tokens are still valid, don't wipe them
    return null
  } else {
    // 401/400 — refresh token is invalid or expired
    clearTokens()
    return null
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

/**
 * fetch() wrapper that attaches the Bearer token and automatically
 * attempts a token refresh on 401 before giving up.
 */
export async function authFetch(url, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
    Authorization: `Bearer ${getAccessToken()}`,
  }

  let response = await fetch(url, { ...options, headers })

  if (response.status === 401) {
    const newToken = await refreshOnce()
    if (newToken) {
      headers.Authorization = `Bearer ${newToken}`
      response = await fetch(url, { ...options, headers })
    }
  }

  return response
}
