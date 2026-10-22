import { useState, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  useGetMeApiV1UsersMeGet,
  useEditProfileApiV1UsersMePatch,
  getGetMeApiV1UsersMeGetQueryKey,
} from '@/api/generated/👤-users/👤-users'
import { useDeletePfpApiV1UsersMePfpDelete } from '@/api/generated/🖼-user-profile-picture/🖼-user-profile-picture'
import { Avatar, AvatarImage, AvatarFallback } from '@/shared/ui/avatar'
import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import { Skeleton } from '@/shared/ui/skeleton'
import { Camera, Trash2, Check, X } from 'lucide-react'
import { toast } from 'sonner'
import { SettingsSection, SettingsRow } from './SettingsSection'
import { AvatarUploader, AvatarPreviewModal } from './AvatarUploader'
import { getHttpStatus } from '../lib/http-error'
import defaultPfp from '@/assets/defaults/default-pfp.webp'

const usernameSchema = z.object({
  username: z
    .string()
    .min(5, 'Имя пользователя должно быть не менее 5 символов')
    .max(16, 'Имя пользователя должно быть не более 16 символов')
    .regex(
      /^[a-zA-Z0-9][a-zA-Z0-9_-]*$/,
      'Только буквы, цифры, дефис и подчёркивание'
    ),
})

const emailSchema = z.object({
  email: z.string().email('Некорректный email'),
})


export function ProfileSection() {
  const queryClient = useQueryClient()
  const { data: me, isLoading } = useGetMeApiV1UsersMeGet()
  const { mutate: editProfile } = useEditProfileApiV1UsersMePatch()
  const { mutate: deletePfp } = useDeletePfpApiV1UsersMePfpDelete()

  const [editingField, setEditingField] = useState<'username' | 'email' | null>(null)
  const [avatarModalOpen, setAvatarModalOpen] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [fileObjectUrl, setFileObjectUrl] = useState<string | null>(null)
  const [fileDimensions, setFileDimensions] = useState<{ width: number; height: number } | null>(
    null
  )
  const fileInputRef = useRef<HTMLInputElement>(null)

  const usernameForm = useForm({
    resolver: zodResolver(usernameSchema),
    defaultValues: { username: me?.username || '' },
  })

  const emailForm = useForm({
    resolver: zodResolver(emailSchema),
    defaultValues: { email: me?.email || '' },
  })

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    if (file.size > 10 * 1024 * 1024) {
      toast.error('Файл слишком большой', {
        description: 'Максимальный размер — 10 МБ',
      })
      return
    }

    // Clean up previous objectURL
    if (fileObjectUrl) {
      URL.revokeObjectURL(fileObjectUrl)
    }

    try {
      // Create ImageBitmap to get dimensions (with EXIF handling)
      const bitmap = await createImageBitmap(file)
      const url = URL.createObjectURL(file)
      setSelectedFile(file)
      setFileObjectUrl(url)
      setFileDimensions({ width: bitmap.width, height: bitmap.height })
      setAvatarModalOpen(true)
    } catch {
      toast.error('Не удалось обработать изображение')
    }
  }

  const handleDeleteAvatar = () => {
    deletePfp(undefined, {
      onSuccess: () => {
        queryClient.invalidateQueries({
          queryKey: getGetMeApiV1UsersMeGetQueryKey(),
        })
        toast.success('Фото удалено')
      },
      onError: () => {
        toast.error('Не удалось удалить фото')
      },
    })
  }


  const handleUsernameSubmit = (data: { username: string }) => {
    if (data.username === me?.username) {
      setEditingField(null)
      return
    }

    editProfile(
      { data: { username: data.username } },
      {
        onSuccess: (user) => {
          queryClient.setQueryData(getGetMeApiV1UsersMeGetQueryKey(), user)
          toast.success('Имя пользователя изменено')
          setEditingField(null)
        },
        onError: (error) => {
          const status = getHttpStatus(error)
          if (status === 409 || status === 400 || status === 422) {
            usernameForm.setError('username', {
              message: 'Это имя уже занято или недопустимо',
            })
          } else {
            toast.error('Не удалось изменить имя пользователя')
          }
        },
      }
    )
  }

  const handleEmailSubmit = (data: { email: string }) => {
    if (data.email === me?.email) {
      setEditingField(null)
      return
    }

    editProfile(
      { data: { email: data.email } },
      {
        onSuccess: (user) => {
          queryClient.setQueryData(getGetMeApiV1UsersMeGetQueryKey(), user)
          toast.success('Email изменён')
          setEditingField(null)
        },
        onError: (error) => {
          const status = getHttpStatus(error)
          if (status === 409 || status === 400 || status === 422) {
            emailForm.setError('email', {
              message: 'Этот email уже используется или некорректен',
            })
          } else {
            toast.error('Не удалось изменить email')
          }
        },
      }
    )
  }

  if (isLoading) {
    return (
      <SettingsSection title="Профиль">
        <div className="p-4 space-y-4">
          <div className="flex items-start gap-4">
            <Skeleton className="w-[72px] h-[72px] rounded-full" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-6 w-32" />
              <Skeleton className="h-4 w-48" />
              <Skeleton className="h-4 w-40" />
            </div>
          </div>
        </div>
        <SettingsRow label="Имя пользователя" isLast={false}>
          <Skeleton className="h-9 w-24" />
        </SettingsRow>
        <SettingsRow label="Email" isLast>
          <Skeleton className="h-9 w-24" />
        </SettingsRow>
      </SettingsSection>
    )
  }

  if (!me) return null

  const createdDate = new Intl.DateTimeFormat('ru-RU', {
    month: 'long',
    year: 'numeric',
  }).format(new Date(me.created_at))

  return (
    <>
      <SettingsSection title="Профиль">
        <div className="p-4 space-y-4 border-b border-border/60">
          <div className="flex items-start gap-4">
            <Avatar className="w-[72px] h-[72px]">
              <AvatarImage src={me.pfp_url || defaultPfp} alt={me.username} />
              <AvatarFallback>{me.username[0]?.toUpperCase()}</AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <div className="font-serif text-[22px] font-semibold leading-tight">
                {me.username}
              </div>
              <div className="text-sm text-muted-foreground mt-1">{me.email}</div>
              <div className="text-sm text-muted-foreground mt-0.5">
                Аккаунт создан {createdDate}
              </div>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => fileInputRef.current?.click()}
            >
              <Camera className="w-4 h-4 mr-2" strokeWidth={1.75} />
              Изменить фото
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDeleteAvatar}
              disabled={me.pfp_url?.includes('defaults/default-pfp.webp')}
            >
              <Trash2 className="w-4 h-4 mr-2" strokeWidth={1.75} />
              Удалить фото
            </Button>
            <AvatarUploader onFileSelect={handleFileSelect} inputRef={fileInputRef} />
          </div>
        </div>

        <SettingsRow label="Имя пользователя" isLast={false}>
          {editingField === 'username' ? (
            <form
              onSubmit={usernameForm.handleSubmit(handleUsernameSubmit)}
              className="flex items-start gap-2"
            >
              <div className="space-y-1">
                <Input
                  {...usernameForm.register('username')}
                  className="h-9 w-48"
                  autoFocus
                />
                {usernameForm.formState.errors.username && (
                  <p className="text-xs text-destructive">
                    {usernameForm.formState.errors.username.message}
                  </p>
                )}
              </div>
              <Button type="submit" size="sm" variant="default">
                <Check className="w-4 h-4" />
                <span className="sr-only">Сохранить</span>
              </Button>
              <Button
                type="button"
                size="sm"
                variant="ghost"
                onClick={() => {
                  setEditingField(null)
                  usernameForm.reset({ username: me.username })
                }}
              >
                <X className="w-4 h-4" />
                <span className="sr-only">Отмена</span>
              </Button>
            </form>
          ) : (
            <>
              <span className="text-sm text-muted-foreground">{me.username}</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  usernameForm.reset({ username: me.username })
                  setEditingField('username')
                }}
              >
                Изменить
              </Button>
            </>
          )}
        </SettingsRow>

        <SettingsRow label="Email" isLast>
          {editingField === 'email' ? (
            <form
              onSubmit={emailForm.handleSubmit(handleEmailSubmit)}
              className="flex items-start gap-2"
            >
              <div className="space-y-1">
                <Input
                  {...emailForm.register('email')}
                  type="email"
                  className="h-9 w-48"
                  autoFocus
                />
                {emailForm.formState.errors.email && (
                  <p className="text-xs text-destructive">
                    {emailForm.formState.errors.email.message}
                  </p>
                )}
              </div>
              <Button type="submit" size="sm" variant="default">
                <Check className="w-4 h-4" />
                <span className="sr-only">Сохранить</span>
              </Button>
              <Button
                type="button"
                size="sm"
                variant="ghost"
                onClick={() => {
                  setEditingField(null)
                  emailForm.reset({ email: me.email })
                }}
              >
                <X className="w-4 h-4" />
                <span className="sr-only">Отмена</span>
              </Button>
            </form>
          ) : (
            <>
              <span className="text-sm text-muted-foreground">{me.email}</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  emailForm.reset({ email: me.email })
                  setEditingField('email')
                }}
              >
                Изменить
              </Button>
            </>
          )}
        </SettingsRow>
      </SettingsSection>

      <AvatarPreviewModal
        open={avatarModalOpen}
        onOpenChange={(open) => {
          setAvatarModalOpen(open)
          if (!open && fileObjectUrl) {
            URL.revokeObjectURL(fileObjectUrl)
            setFileObjectUrl(null)
            setSelectedFile(null)
            setFileDimensions(null)
          }
        }}
        file={selectedFile}
        fileObjectUrl={fileObjectUrl}
        fileDimensions={fileDimensions}
      />
    </>
  )
}

