let accessToken: string | null = null
let refreshToken: string | null = null

const REFRESH_IN_FLIGHT_KEY = 'refresh_in_flight'

export function getAccessToken(): string | null {
  return accessToken
}

export function getRefreshToken(): string | null {
  return refreshToken
}

export function setTokens(access: string, refresh: string) {
  accessToken = access
  refreshToken = refresh
  localStorage.setItem('access_token', access)
  localStorage.setItem('refresh_token', refresh)
}

export function clearTokens() {
  accessToken = null
  refreshToken = null
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

export function loadTokensFromStorage() {
  accessToken = localStorage.getItem('access_token')
  refreshToken = localStorage.getItem('refresh_token')
}

type RefreshResponse = {
  user: unknown
  token: {
    access_token: string
    refresh_token: string
  }
}

async function refreshAccessToken(): Promise<boolean> {
  const refresh = getRefreshToken()
  if (!refresh) return false

  // Single-flight refresh: prevent concurrent refresh calls
  if (localStorage.getItem(REFRESH_IN_FLIGHT_KEY)) {
    // Wait for the in-flight refresh to complete
    await new Promise((resolve) => setTimeout(resolve, 100))
    return !!getAccessToken()
  }

  try {
    localStorage.setItem(REFRESH_IN_FLIGHT_KEY, '1')

    const response = await fetch(
      `${import.meta.env.VITE_API_URL}/api/v1/users/refresh`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refresh }),
      }
    )

    if (!response.ok) {
      clearTokens()
      // Redirect to login
      window.location.href = '/login'
      return false
    }

    const data: RefreshResponse = await response.json()
    setTokens(data.token.access_token, data.token.refresh_token)
    return true
  } catch {
    clearTokens()
    window.location.href = '/login'
    return false
  } finally {
    localStorage.removeItem(REFRESH_IN_FLIGHT_KEY)
  }
}

export async function customFetch<T>(
  url: string,
  options?: RequestInit
): Promise<T> {
  const baseURL = import.meta.env.VITE_API_URL || ''
  const fullURL = url.startsWith('http') ? url : `${baseURL}${url}`

  // Debug logging - ALWAYS log to see what's happening in production
  console.log('[customFetch] VITE_API_URL:', import.meta.env.VITE_API_URL)
  console.log('[customFetch] baseURL:', baseURL)
  console.log('[customFetch] url:', url)
  console.log('[customFetch] fullURL:', fullURL)

  const token = getAccessToken()
  const headers = new Headers(options?.headers)
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  let response: Response
  try {
    response = await fetch(fullURL, {
      ...options,
      headers,
    })
    console.log('[customFetch] response status:', response.status)
  } catch (error) {
    console.error('[customFetch] fetch error:', error)
    throw error
  }

  // Handle 401: try to refresh token once
  if (response.status === 401 && getRefreshToken()) {
    const refreshed = await refreshAccessToken()
    if (refreshed) {
      // Retry the original request with new token
      const newToken = getAccessToken()
      if (newToken) {
        headers.set('Authorization', `Bearer ${newToken}`)
      }
      response = await fetch(fullURL, {
        ...options,
        headers,
      })
    }
  }

  // Handle 404 for /users/me after token refresh fails or DB reset
  // Проверяем точное совпадение с /api/v1/users/me, чтобы не затрагивать подпути
  // (например, /api/v1/users/me/pfp возвращает 404 при отсутствии фото — это не logout)
  if (response.status === 404 && /\/api\/v1\/users\/me$/.test(fullURL)) {
    clearTokens()
    window.location.href = '/login'
    throw new Error('User not found. Please log in again.')
  }

  if (!response.ok) {
    const errorText = await response.text()
    console.error('[customFetch] HTTP error:', response.status, errorText)
    throw new Error(`HTTP ${response.status}: ${response.statusText}`)
  }

  // Handle empty responses (204 No Content, DELETE requests)
  if (response.status === 204 || response.headers.get('content-length') === '0') {
    return undefined as T
  }

  return response.json()
}

export async function customFetchBlob(
  url: string,
  options?: RequestInit
): Promise<{ blob: Blob; filename: string | null }> {
  const baseURL = import.meta.env.VITE_API_URL || ''
  const fullURL = url.startsWith('http') ? url : `${baseURL}${url}`

  const doFetch = () => {
    const headers = new Headers(options?.headers)
    const token = getAccessToken()
    if (token) headers.set('Authorization', `Bearer ${token}`)
    return fetch(fullURL, { ...options, headers })
  }

  let response = await doFetch()
  if (response.status === 401 && getRefreshToken()) {
    if (await refreshAccessToken()) response = await doFetch()
  }
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`)
  }

  const disposition = response.headers.get('content-disposition')
  const match = disposition ? /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(disposition) : null
  return { blob: await response.blob(), filename: match ? decodeURIComponent(match[1]) : null }
}
