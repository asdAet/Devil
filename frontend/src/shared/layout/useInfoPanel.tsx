/* eslint-disable react-refresh/only-export-components */
import { createContext, useCallback, useContext, useState, type ReactNode } from 'react'

type InfoPanelContent = 'profile' | 'group' | 'search' | 'direct' | null

type InfoPanelState = {
  isOpen: boolean
  content: InfoPanelContent
  targetId: string | null
  open: (content: NonNullable<InfoPanelContent>, targetId?: string | null) => void
  close: () => void
  toggle: (content: NonNullable<InfoPanelContent>, targetId?: string | null) => void
}

const InfoPanelCtx = createContext<InfoPanelState>({
  isOpen: false,
  content: null,
  targetId: null,
  open: () => {},
  close: () => {},
  toggle: () => {},
})

export function InfoPanelProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<{ content: InfoPanelContent; targetId: string | null }>({
    content: null,
    targetId: null,
  })

  const open = useCallback((content: NonNullable<InfoPanelContent>, targetId?: string | null) => {
    setState({ content, targetId: targetId ?? null })
  }, [])

  const close = useCallback(() => {
    setState({ content: null, targetId: null })
  }, [])

  const toggle = useCallback((content: NonNullable<InfoPanelContent>, targetId?: string | null) => {
    setState((prev) => {
      if (prev.content === content && prev.targetId === (targetId ?? null)) {
        return { content: null, targetId: null }
      }
      return { content, targetId: targetId ?? null }
    })
  }, [])

  const value: InfoPanelState = {
    isOpen: state.content !== null,
    content: state.content,
    targetId: state.targetId,
    open,
    close,
    toggle,
  }

  return <InfoPanelCtx.Provider value={value}>{children}</InfoPanelCtx.Provider>
}

export function useInfoPanel() {
  return useContext(InfoPanelCtx)
}

