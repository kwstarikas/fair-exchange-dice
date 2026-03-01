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
    const refreshResponse = await fetch('/api/auth/token/refresh/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: getRefreshToken() }),
    })

    if (refreshResponse.ok) {
      const data = await refreshResponse.json()
      if (!data.access) {
        clearTokens()
        return response
      }
      if (!data.refresh) {
        console.warn('Server did not return a new refresh token — rotation may be misconfigured.')
      }
      storeTokens({
        access: data.access,
        refresh: data.refresh ?? getRefreshToken(),
      })
      headers.Authorization = `Bearer ${data.access}`
      response = await fetch(url, { ...options, headers })
    } else {
      clearTokens()
    }
  }

  return response
}
