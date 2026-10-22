import { useGetMeApiV1UsersMeGet } from '@/api/generated/👤-users/👤-users'
import { Skeleton } from '@/shared/ui/skeleton'
import { ProfileSection } from '../components/ProfileSection'
import { AppearanceSection } from '../components/AppearanceSection'
import { RegionSection } from '../components/RegionSection'
import { SecuritySection } from '../components/SecuritySection'
import { IntegrationsSection } from '../components/IntegrationsSection'
import { AccountSection } from '../components/AccountSection'

export function SettingsPage() {
  const { isLoading } = useGetMeApiV1UsersMeGet()

  if (isLoading) {
    return (
      <div className="max-w-[720px] mx-auto px-4 lg:px-8 py-8 space-y-10">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-64 w-full rounded-2xl" />
        <Skeleton className="h-32 w-full rounded-2xl" />
        <Skeleton className="h-32 w-full rounded-2xl" />
      </div>
    )
  }

  return (
    <div className="max-w-[720px] mx-auto px-4 lg:px-8 py-8 space-y-10">
      <h1 className="font-serif text-[32px] font-semibold leading-tight">
        Настройки
      </h1>
      <ProfileSection />
      <AppearanceSection />
      <RegionSection />
      <SecuritySection />
      <IntegrationsSection />
      <AccountSection />
    </div>
  )
}

