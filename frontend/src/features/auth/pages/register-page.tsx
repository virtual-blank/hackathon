import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { useSignUpApiV1UsersSignUpPost } from '@/api/generated/👤-users/👤-users'
import { setTokens } from '@/api/mutator'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { toast } from 'sonner'

const registerSchema = z.object({
  username: z
    .string()
    .min(5, 'Имя пользователя должно быть не менее 5 символов')
    .max(16, 'Имя пользователя должно быть не более 16 символов')
    .regex(/^[a-zA-Z0-9][a-zA-Z0-9_-]*$/, 'Только буквы, цифры, дефис и подчёркивание'),
  email: z.string().email('Некорректный email'),
  password: z.string().min(1, 'Пароль обязателен'),
})

type RegisterFormData = z.infer<typeof registerSchema>

export default function RegisterPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { mutate: signUp, isPending } = useSignUpApiV1UsersSignUpPost()

  const {
    register,
    handleSubmit,
    formState: { errors },
    setError,
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  })

  const onSubmit = (data: RegisterFormData) => {
    signUp(
      { data },
      {
        onSuccess: (response) => {
          setTokens(response.token.access_token, response.token.refresh_token)
          queryClient.clear()
          toast.success('Регистрация прошла успешно')
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
                if (field === 'username' || field === 'email' || field === 'password') {
                  setError(field, { message: err.msg })
                }
              })
            }
          } else {
            toast.error('Ошибка регистрации. Попробуйте ещё раз.')
          }
        },
      }
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold">Регистрация</CardTitle>
          <CardDescription>
            Создайте аккаунт, чтобы начать отслеживать привычки
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
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                {...register('email')}
                placeholder="example@example.com"
                aria-invalid={!!errors.email}
              />
              {errors.email && (
                <p className="text-sm text-destructive">{errors.email.message}</p>
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
              {isPending ? 'Регистрация...' : 'Зарегистрироваться'}
            </Button>
          </form>
          <p className="text-sm text-center text-muted-foreground mt-4">
            Уже есть аккаунт?{' '}
            <a href="/login" className="text-primary hover:underline">
              Войти
            </a>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
