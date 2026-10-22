import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type AppShellStore = {
  sidebarCollapsed: boolean
  createHabitSheetOpen: boolean
  setSidebarCollapsed: (collapsed: boolean) => void
  setCreateHabitSheetOpen: (open: boolean) => void
}

export const useAppShellStore = create<AppShellStore>()(
  persist(
    (set) => ({
      sidebarCollapsed: false,
      createHabitSheetOpen: false,
      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
      setCreateHabitSheetOpen: (open) => set({ createHabitSheetOpen: open }),
    }),
    {
      name: 'app-shell-storage',
      partialize: (state) => ({ sidebarCollapsed: state.sidebarCollapsed }),
    }
  )
)
