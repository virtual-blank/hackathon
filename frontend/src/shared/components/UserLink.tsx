import { Link, useNavigate } from 'react-router-dom'
import { useGetMeApiV1UsersMeGet } from '@/api/generated/👤-users/👤-users'
import { cn } from '@/shared/lib/utils'

type UserLinkProps = {
  userId: string
  username: string
  pfpUrl: string
  children: React.ReactNode
  className?: string
  onClick?: (e: React.MouseEvent) => void
}

export function UserLink({ userId, username, pfpUrl, children, className, onClick }: UserLinkProps) {
  const { data: me } = useGetMeApiV1UsersMeGet()
  const navigate = useNavigate()

  const handleClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
    if (onClick) {
      onClick(e)
    }
    
    // Redirect to /profile if viewing self
    if (me && userId === me.id) {
      e.preventDefault()
      navigate('/profile')
    }
  }

  const to = me && userId === me.id ? '/profile' : `/users/${userId}`
  const state = { id: userId, username, pfp_url: pfpUrl }

  return (
    <Link
      to={to}
      state={state}
      onClick={handleClick}
      className={cn(
        'transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded-sm',
        className
      )}
    >
      {children}
    </Link>
  )
}
