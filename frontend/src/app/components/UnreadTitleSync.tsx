import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { useUnreadMessages } from '@/features/social/hooks/useUnreadMessages'

export function UnreadTitleSync() {
  const { hasUnreadMessages } = useUnreadMessages()
  const { pathname } = useLocation()
  
  useEffect(() => {
    const clean = document.title.replace(/^● /, '')
    document.title = hasUnreadMessages ? `● ${clean}` : clean
  }, [hasUnreadMessages, pathname])
  
  return null
}
