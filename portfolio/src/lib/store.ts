import { create } from 'zustand'

type AppState = {
  /** The preloader has finished and the intro animation may start. */
  ready: boolean
  menuOpen: boolean
  activeProject: number
  setReady: () => void
  setMenuOpen: (open: boolean) => void
  setActiveProject: (index: number) => void
}

export const useApp = create<AppState>((set) => ({
  ready: false,
  menuOpen: false,
  activeProject: 0,
  setReady: () => set({ ready: true }),
  setMenuOpen: (menuOpen) => set({ menuOpen }),
  setActiveProject: (activeProject) => set({ activeProject }),
}))

/**
 * Progress signals the preloader waits for. Each loader reports a value in [0, 1]
 * and the preloader shows their average.
 */
type LoadState = {
  tasks: Record<string, number>
  report: (task: string, value: number) => void
}

export const useLoad = create<LoadState>((set) => ({
  tasks: { fonts: 0, backdrop: 0, scene: 0 },
  report: (task, value) => set((s) => ({ tasks: { ...s.tasks, [task]: Math.max(s.tasks[task] ?? 0, value) } })),
}))
