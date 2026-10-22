import { Navigate, Outlet } from 'react-router-dom'
import { getAccessToken } from '@/api/mutator'

export function RequireAuth() {
  const token = getAccessToken()

  if (!token) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}

export function RequireGuest() {
  const token = getAccessToken()

  if (token) {
    return <Navigate to="/" replace />
  }

  return <Outlet />
}
