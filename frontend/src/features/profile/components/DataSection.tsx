import { Button } from '@/shared/ui/button'
import { useNavigate } from 'react-router-dom'
import { SettingsSection, SettingsRow } from './SettingsSection'

export function DataSection() {
  const navigate = useNavigate()

  return (
    <SettingsSection
      title="Данные"
      description="Управление вашими данными"
    >
      <SettingsRow
        label="Экспорт данных"
        description="Скачайте привычки и историю в CSV"
        isLast
      >
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/export')}
        >
          Открыть
        </Button>
      </SettingsRow>
    </SettingsSection>
  )
}
