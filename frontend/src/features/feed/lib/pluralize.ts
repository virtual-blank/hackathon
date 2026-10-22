export function pluralizeCount(count: number): string {
  const rules = new Intl.PluralRules('ru')
  const category = rules.select(count)

  const forms: Record<string, string> = {
    one: 'раз',
    few: 'раза',
    many: 'раз',
    other: 'раз',
  }

  return forms[category] || forms.other
}
