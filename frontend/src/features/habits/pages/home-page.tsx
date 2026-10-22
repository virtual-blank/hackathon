import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'

export default function HomePage() {
  return (
    <div className="container mx-auto p-4">
      <div className="max-w-4xl mx-auto space-y-6">
        <header>
          <h1 className="text-4xl font-bold mb-2">Сегодня</h1>
          <p className="text-muted-foreground">Ваши привычки на сегодня</p>
        </header>

        <Card>
          <CardHeader>
            <CardTitle>Добро пожаловать!</CardTitle>
            <CardDescription>
              Фронтенд настроен. Начните создавать привычки.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Это placeholder-страница. Реальная функциональность будет добавлена
              позднее.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
