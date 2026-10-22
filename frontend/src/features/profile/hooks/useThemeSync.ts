import { useEffect, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import {
  useGetMeApiV1UsersMeGet,
  useEditProfileApiV1UsersMePatch,
  getGetMeApiV1UsersMeGetQueryKey,
} from '@/api/generated/👤-users/👤-users'
import { useThemeStore } from '@/shared/lib/theme'

export function useThemeSync() {
  const { data: me } = useGetMeApiV1UsersMeGet()
  const theme = useThemeStore((s) => s.theme)
  const setTheme = useThemeStore((s) => s.setTheme)
  const queryClient = useQueryClient()
  const { mutate } = useEditProfileApiV1UsersMePatch()
  const hydratedRef = useRef(false)

  // 1) One-time hydration: server theme takes precedence
  useEffect(() => {
    if (!me || hydratedRef.current) return
    if (me.theme !== theme) {
      setTheme(me.theme)
    }
    hydratedRef.current = true
  }, [me, theme, setTheme])

  // 2) Sync any theme change to server
  useEffect(() => {
    if (!me || !hydratedRef.current || me.theme === theme) return
    mutate(
      { data: { theme } },
      {
        onSuccess: (user) =>
          queryClient.setQueryData(getGetMeApiV1UsersMeGetQueryKey(), user),
      }
    )
  }, [theme, me, mutate, queryClient])
}

export function ThemeSync() {
  useThemeSync()
  return null
}

