import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { AppShell } from './app-shell'
import { RequireAuth, RequireGuest } from './route-guards'

// Lazy-load pages
import { lazy } from 'react'

const LoginPage = lazy(() => import('@/features/auth/pages/login-page'))
const RegisterPage = lazy(() => import('@/features/auth/pages/register-page'))
const TodayPage = lazy(() => import('@/features/habits/pages/TodayPage').then(m => ({ default: m.TodayPage })))
const FeedPage = lazy(() => import('@/features/feed/pages/FeedPage').then(m => ({ default: m.FeedPage })))
const FriendsPage = lazy(() => import('@/features/friends/pages/FriendsPage').then(m => ({ default: m.FriendsPage })))
const NotificationsPage = lazy(() => import('@/features/notifications/pages/NotificationsPage').then(m => ({ default: m.NotificationsPage })))
const ChatPage = lazy(() => import('@/features/social/pages/ChatPage').then(m => ({ default: m.ChatPage })))
const ExportPage = lazy(() => import('@/features/exports/pages/ExportPage').then(m => ({ default: m.ExportPage })))
const ProfilePage = lazy(() => import('@/features/profile/pages/ProfilePage'))
const UserProfilePage = lazy(() => import('@/features/profile/pages/UserProfilePage').then(m => ({ default: m.UserProfilePage })))
const SettingsPage = lazy(() => import('@/features/profile/pages/SettingsPage').then(m => ({ default: m.SettingsPage })))
const DesignPage = lazy(() => import('@/features/design/design-page'))

const router = createBrowserRouter([
  {
    element: <AppShell />,
    children: [
      {
        element: <RequireGuest />,
        children: [
          {
            path: '/login',
            element: <LoginPage />,
          },
          {
            path: '/register',
            element: <RegisterPage />,
          },
        ],
      },
      {
        element: <RequireAuth />,
        children: [
          {
            path: '/',
            element: <TodayPage />,
          },
          {
            path: '/feed',
            element: <FeedPage />,
          },
          {
            path: '/friends',
            element: <FriendsPage />,
          },
          {
            path: '/notifications',
            element: <NotificationsPage />,
          },
          {
            path: '/chat',
            element: <ChatPage />,
          },
          {
            path: '/export',
            element: <ExportPage />,
          },
          {
            path: '/profile',
            element: <ProfilePage />,
          },
          {
            path: '/users/:userId',
            element: <UserProfilePage />,
          },
          {
            path: '/settings',
            element: <SettingsPage />,
          },
        ],
      },
      {
        path: '/_design',
        element: <DesignPage />,
      },
    ],
  },
])

export function Router() {
  return <RouterProvider router={router} />
}

