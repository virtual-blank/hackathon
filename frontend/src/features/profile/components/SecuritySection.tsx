import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  useChangePasswordApiV1UsersPasswordPatch,
  getGetMeApiV1UsersMeGetQueryKey,
} from '@/api/generated/👤-users/👤-users'
import { setTokens } from '@/api/mutator'
import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { Eye, EyeOff } from 'lucide-react'
import { toast } from 'sonner'
import { SettingsSection, SettingsRow } from './SettingsSection'
import { ResponsiveModal } from '@/shared/components/ResponsiveModal'
import { getHttpStatus } from '../lib/http-error'

const passwordSchema = z
  .object({
    current_password: z.string().min(1, 'Введите текущий пароль'),
    new_password: z.string().min(1, 'Введите новый пароль'),
    confirm_password: z.string().min(1, 'Повторите новый пароль'),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: 'Пароли не совпадают',
    path: ['confirm_password'],
  })
  .refine((data) => data.new_password !== data.current_password, {
    message: 'Новый пароль должен отличаться от текущего',
    path: ['new_password'],
  })

type PasswordFormData = z.infer<typeof passwordSchema>

export function SecuritySection() {
  const queryClient = useQueryClient()
  const { mutate: changePassword, isPending } = useChangePasswordApiV1UsersPasswordPatch()
  const [modalOpen, setModalOpen] = useState(false)
  const [show, setShow] = useState({ current: false, new: false, confirm: false })

  const { register, handleSubmit, formState: { errors }, setError, reset } = useForm<PasswordFormData>({
    resolver: zodResolver(passwordSchema),
    defaultValues: { current_password: '', new_password: '', confirm_password: '' },
  })

  const onSubmit = (data: PasswordFormData) => {
    changePassword(
      { data: { current_password: data.current_password, new_password: data.new_password } },
      {
        onSuccess: (response) => {
          setTokens(response.token.access_token, response.token.refresh_token)
          queryClient.setQueryData(getGetMeApiV1UsersMeGetQueryKey(), response.user)
          toast.success('Пароль изменён')
          setModalOpen(false)
          reset()
        },
        onError: (error) => {
          const status = getHttpStatus(error)
          if ([400, 401, 403, 422].includes(status || 0)) {
            setError('current_password', { message: 'Неверный текущий пароль' })
          } else {
            toast.error('Не удалось изменить пароль')
          }
        },
      }
    )
  }

  return (
    <>
      <SettingsSection title="Безопасность">
        <SettingsRow label="Пароль" description="Измените пароль для входа" isLast>
          <Button variant="ghost" size="sm" onClick={() => setModalOpen(true)}>Изменить</Button>
        </SettingsRow>
      </SettingsSection>

      <ResponsiveModal open={modalOpen} onOpenChange={(open) => { setModalOpen(open); if (!open) reset() }} title="Смена пароля">
        <form onSubmit={handleSubmit(onSubmit)} className="p-4 space-y-4">
          <div className="space-y-2">
            <Label htmlFor="current_password">Текущий пароль</Label>
            <div className="relative">
              <Input id="current_password" type={show.current ? 'text' : 'password'} autoComplete="current-password" {...register('current_password')} className="pr-10" />
              <button type="button" onClick={() => setShow({...show, current: !show.current})} className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 text-muted-foreground hover:text-foreground" aria-label={show.current ? 'Скрыть' : 'Показать'}>
                {show.current ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            {errors.current_password && <p className="text-sm text-destructive">{errors.current_password.message}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="new_password">Новый пароль</Label>
            <div className="relative">
              <Input id="new_password" type={show.new ? 'text' : 'password'} autoComplete="new-password" {...register('new_password')} className="pr-10" />
              <button type="button" onClick={() => setShow({...show, new: !show.new})} className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 text-muted-foreground hover:text-foreground" aria-label={show.new ? 'Скрыть' : 'Показать'}>
                {show.new ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            {errors.new_password && <p className="text-sm text-destructive">{errors.new_password.message}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirm_password">Повторите новый пароль</Label>
            <div className="relative">
              <Input id="confirm_password" type={show.confirm ? 'text' : 'password'} autoComplete="new-password" {...register('confirm_password')} className="pr-10" />
              <button type="button" onClick={() => setShow({...show, confirm: !show.confirm})} className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 text-muted-foreground hover:text-foreground" aria-label={show.confirm ? 'Скрыть' : 'Показать'}>
                {show.confirm ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            {errors.confirm_password && <p className="text-sm text-destructive">{errors.confirm_password.message}</p>}
          </div>

          <div className="flex gap-2 pt-2">
            <Button type="submit" disabled={isPending} className="flex-1">{isPending ? 'Сохранение...' : 'Сохранить'}</Button>
            <Button type="button" variant="outline" onClick={() => { setModalOpen(false); reset() }} disabled={isPending}>Отмена</Button>
          </div>
        </form>
      </ResponsiveModal>
    </>
  )
}
