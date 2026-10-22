import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { useLoginApiV1UsersLoginPost } from '@/api/generated/👤-users/👤-users'
import { setTokens } from '@/api/mutator'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { toast } from 'sonner'

const loginSchema = z.object({
  username: z.string().min(5, 'Имя пользователя должно быть не менее 5 символов').max(16, 'Имя пользователя должно быть не более 16 символов'),
  password: z.string().min(1, 'Пароль обязателен'),
})

type LoginFormData = z.infer<typeof loginSchema>

const DEV_ACCOUNTS = [
  { username: 'alexandra_sfm', password: 'Password_8NgPlxN', label: 'Alexandra' },
  { username: 'dima_kolesnikov', password: 'Password_8NgPlxN', label: 'Dima' },
]

export default function LoginPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { mutate: login, isPending } = useLoginApiV1UsersLoginPost()

  const {
    register,
    handleSubmit,
    formState: { errors },
    setError,
    setValue,
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  })

  const onSubmit = (data: LoginFormData) => {
    login(
      { data },
      {
        onSuccess: (response) => {
          setTokens(response.token.access_token, response.token.refresh_token)
          queryClient.clear()
          toast.success('Вход выполнен успешно')
          navigate('/')
        },
        onError: (error) => {
          if (error && typeof error === 'object' && 'detail' in error) {
            const detail = error.detail as string | Array<{ loc: string[]; msg: string }>
            if (typeof detail === 'string') {
              toast.error(detail)
            } else if (Array.isArray(detail)) {
              detail.forEach((err) => {
                const field = err.loc[err.loc.length - 1]
                if (field === 'username' || field === 'password') {
                  setError(field, { message: err.msg })
                }
              })
            }
          } else {
            toast.error('Ошибка входа. Проверьте данные.')
          }
        },
      }
    )
  }

  const quickLogin = (username: string, password: string) => {
    setValue('username', username)
    setValue('password', password)
    handleSubmit(onSubmit)()
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-4 bg-background">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="font-display text-2xl font-semibold">Вход</CardTitle>
          <CardDescription>
            Введите свои данные для входа в аккаунт
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">Имя пользователя</Label>
              <Input
                id="username"
                type="text"
                autoComplete="username"
                {...register('username')}
                placeholder="username"
                aria-invalid={!!errors.username}
              />
              {errors.username && (
                <p className="text-sm text-destructive">{errors.username.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Пароль</Label>
              <Input
                id="password"
                type="password"
                {...register('password')}
                placeholder="••••••••"
                aria-invalid={!!errors.password}
              />
              {errors.password && (
                <p className="text-sm text-destructive">{errors.password.message}</p>
              )}
            </div>
            <Button type="submit" className="w-full" disabled={isPending}>
              {isPending ? 'Вход...' : 'Войти'}
            </Button>
          </form>
          
          {import.meta.env.DEV && (
            <div className="mt-6 pt-4 border-t border-border">
              <p className="text-xs text-muted-foreground mb-2">Быстрый вход (Dev)</p>
              <div className="flex gap-2">
                {DEV_ACCOUNTS.map((account) => (
                  <Button
                    key={account.username}
                    type="button"
                    variant="secondary"
                    size="sm"
                    className="flex-1 text-xs"
                    onClick={() => quickLogin(account.username, account.password)}
                    disabled={isPending}
                  >
                    {account.label}
                  </Button>
                ))}
              </div>
            </div>
          )}

          <p className="text-sm text-center text-muted-foreground mt-4">
            Нет аккаунта?{' '}
            <a href="/register" className="text-primary hover:underline">
              Зарегистрироваться
            </a>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
