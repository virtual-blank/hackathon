import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { Skeleton } from '@/shared/ui/skeleton'

export default function DesignPage() {
  return (
    <div className="container mx-auto p-8 space-y-12">
      <header>
        <h1 className="text-4xl font-bold mb-2">Дизайн-система</h1>
        <p className="text-muted-foreground">
          Компоненты и стили для разработки
        </p>
      </header>

      {/* Typography */}
      <section className="space-y-4">
        <h2 className="text-2xl font-bold">Типографика</h2>
        <div className="space-y-2">
          <h1 className="text-4xl font-bold">Heading 1</h1>
          <h2 className="text-3xl font-bold">Heading 2</h2>
          <h3 className="text-2xl font-bold">Heading 3</h3>
          <h4 className="text-xl font-bold">Heading 4</h4>
          <p className="text-base">Body text — Inter Variable</p>
          <p className="text-sm text-muted-foreground">
            Muted text for secondary information
          </p>
        </div>
      </section>

      {/* Colors */}
      <section className="space-y-4">
        <h2 className="text-2xl font-bold">Цвета</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="space-y-2">
            <div className="h-16 rounded-lg bg-primary" />
            <p className="text-sm font-medium">Primary</p>
          </div>
          <div className="space-y-2">
            <div className="h-16 rounded-lg bg-secondary" />
            <p className="text-sm font-medium">Secondary</p>
          </div>
          <div className="space-y-2">
            <div className="h-16 rounded-lg bg-streak" />
            <p className="text-sm font-medium">Streak</p>
          </div>
          <div className="space-y-2">
            <div className="h-16 rounded-lg bg-success" />
            <p className="text-sm font-medium">Success</p>
          </div>
          <div className="space-y-2">
            <div className="h-16 rounded-lg bg-destructive" />
            <p className="text-sm font-medium">Destructive</p>
          </div>
          <div className="space-y-2">
            <div className="h-16 rounded-lg bg-info" />
            <p className="text-sm font-medium">Info</p>
          </div>
        </div>
      </section>

      {/* Buttons */}
      <section className="space-y-4">
        <h2 className="text-2xl font-bold">Кнопки</h2>
        <div className="flex flex-wrap gap-4">
          <Button>Default</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="outline">Outline</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="destructive">Destructive</Button>
          <Button variant="link">Link</Button>
        </div>
        <div className="flex flex-wrap gap-4">
          <Button size="sm">Small</Button>
          <Button size="default">Default</Button>
          <Button size="lg">Large</Button>
        </div>
      </section>

      {/* Form inputs */}
      <section className="space-y-4">
        <h2 className="text-2xl font-bold">Формы</h2>
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle>Пример формы</CardTitle>
            <CardDescription>
              Поля ввода с лейблами и валидацией
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Имя</Label>
              <Input id="name" placeholder="Введите имя" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="example@example.com"
              />
            </div>
            <Button className="w-full">Отправить</Button>
          </CardContent>
        </Card>
      </section>

      {/* Cards */}
      <section className="space-y-4">
        <h2 className="text-2xl font-bold">Карточки</h2>
        <div className="grid md:grid-cols-2 gap-4">
          <Card>
            <CardHeader>
              <CardTitle>Карточка с заголовком</CardTitle>
              <CardDescription>Описание карточки</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm">
                Содержимое карточки. Может быть любой контент.
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Еще одна карточка</CardTitle>
              <CardDescription>С описанием</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm">
                Карточки используются для группировки связанного контента.
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Skeleton loaders */}
      <section className="space-y-4">
        <h2 className="text-2xl font-bold">Skeleton Loaders</h2>
        <Card className="max-w-md">
          <CardHeader>
            <Skeleton className="h-6 w-3/4 mb-2" />
            <Skeleton className="h-4 w-full" />
          </CardHeader>
          <CardContent className="space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-5/6" />
            <Skeleton className="h-4 w-4/6" />
          </CardContent>
        </Card>
      </section>
    </div>
  )
}
