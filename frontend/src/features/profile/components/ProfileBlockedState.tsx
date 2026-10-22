import { Lock } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/shared/ui/button'

export function ProfileBlockedState() {
  const navigate = useNavigate()

  const handleBack = () => {
    if (window.history.length > 2) {
      navigate(-1)
    } else {
      navigate('/friends')
    }
  }

  return (
    <div className="min-h-full flex items-center justify-center px-4 py-16">
      <div className="max-w-md w-full text-center space-y-6">
        {/* Lock icon with soft glow */}
        <div className="relative inline-flex items-center justify-center">
          <div className="absolute inset-0 rounded-full bg-muted-foreground/10 blur-[32px]" />
          <div className="relative flex items-center justify-center w-24 h-24 rounded-full bg-surface-muted ring-1 ring-border">
            <Lock className="w-10 h-10 text-muted-foreground" strokeWidth={1.75} />
          </div>
        </div>

        {/* Heading */}
        <div className="space-y-2">
          <h1 className="font-display text-2xl lg:text-3xl font-semibold">
            Упс… Кажется, этот профиль недоступен
          </h1>
          <p className="text-sm text-muted-foreground">
            Возможно, пользователь ограничил доступ к своему профилю
          </p>
        </div>

        {/* Back button */}
        <Button onClick={handleBack} className="mt-6">
          Назад
        </Button>
      </div>
    </div>
  )
}
