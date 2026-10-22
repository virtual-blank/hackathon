import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import {
  useGetMeApiV1UsersMeGet,
  useLogoutApiV1UsersLogoutPost,
  useDeleteAccountApiV1UsersMeDelete,
} from '@/api/generated/👤-users/👤-users'
import { clearTokens } from '@/api/mutator'
import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import { LogOut } from 'lucide-react'
import { toast } from 'sonner'
import { SettingsSection, SettingsRow } from './SettingsSection'
import { ResponsiveModal } from '@/shared/components/ResponsiveModal'

export function AccountSection() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { data: me } = useGetMeApiV1UsersMeGet()
  const { mutate: logout } = useLogoutApiV1UsersLogoutPost()
  const { mutate: deleteAccount, isPending } = useDeleteAccountApiV1UsersMeDelete()
  const [deleteModalOpen, setDeleteModalOpen] = useState(false)
  const [confirmUsername, setConfirmUsername] = useState('')

  const handleLogout = () => {
    logout(undefined, {
      onSettled: () => {
        clearTokens()
        queryClient.clear()
        navigate('/login')
      },
    })
  }

  const handleDeleteAccount = () => {
    deleteAccount(undefined, {
      onSuccess: () => {
        clearTokens()
        queryClient.clear()
        navigate('/login')
        toast.success('Аккаунт удалён')
      },
      onError: () => {
        toast.error('Не удалось удалить аккаунт')
      },
    })
  }

  return (
    <>
      <SettingsSection title="Аккаунт">
        <SettingsRow label="Выйти из аккаунта" isLast>
          <Button variant="secondary" size="sm" onClick={handleLogout}>
            <LogOut className="w-4 h-4 mr-2" strokeWidth={1.75} />
            Выйти
          </Button>
        </SettingsRow>
      </SettingsSection>

      <div className="pt-6 border-t border-destructive/20">
        <SettingsSection
          title="Опасная зона"
          description="Аккаунт, привычки и данные будут удалены без возможности восстановления"
        >
          <SettingsRow
            label="Удалить аккаунт"
            description="Это действие необратимо"
            isLast
          >
            <Button
              variant="destructive"
              size="sm"
              onClick={() => setDeleteModalOpen(true)}
            >
              Удалить аккаунт
            </Button>
          </SettingsRow>
        </SettingsSection>
      </div>

      <ResponsiveModal
        open={deleteModalOpen}
        onOpenChange={setDeleteModalOpen}
        title="Удалить аккаунт?"
        description={`Это действие необратимо. Чтобы подтвердить, введите ваше имя пользователя: ${me?.username || ''}`}
      >
        <div className="p-4 space-y-4">
          <Input
            value={confirmUsername}
            onChange={(e) => setConfirmUsername(e.target.value)}
            placeholder={me?.username}
          />
          <div className="flex gap-2">
            <Button
              variant="destructive"
              onClick={handleDeleteAccount}
              disabled={confirmUsername !== me?.username || isPending}
              className="flex-1"
            >
              {isPending ? 'Удаление...' : 'Удалить навсегда'}
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                setDeleteModalOpen(false)
                setConfirmUsername('')
              }}
              disabled={isPending}
            >
              Отмена
            </Button>
          </div>
        </div>
      </ResponsiveModal>
    </>
  )
}
