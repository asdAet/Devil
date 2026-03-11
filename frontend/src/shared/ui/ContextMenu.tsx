import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react'

import styles from '../../styles/ui/ContextMenu.module.css'

export type ContextMenuItem = {
  label: string
  icon?: ReactNode
  danger?: boolean
  disabled?: boolean
  onClick: () => void
}

type Props = {
  items: ContextMenuItem[]
  x: number
  y: number
  onClose: () => void
}

export function ContextMenu({ items, x, y, onClose }: Props) {
  const ref = useRef<HTMLDivElement>(null)
  const [pos, setPos] = useState({ x, y })

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    let nx = x
    let ny = y
    if (x + rect.width > window.innerWidth - 8) nx = window.innerWidth - rect.width - 8
    if (y + rect.height > window.innerHeight - 8) ny = window.innerHeight - rect.height - 8
    if (nx < 8) nx = 8
    if (ny < 8) ny = 8
    setPos({ x: nx, y: ny })
  }, [x, y])

  useEffect(() => {
    const handleClick = () => onClose()
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('click', handleClick)
    document.addEventListener('contextmenu', handleClick)
    document.addEventListener('keydown', handleKey)
    return () => {
      document.removeEventListener('click', handleClick)
      document.removeEventListener('contextmenu', handleClick)
      document.removeEventListener('keydown', handleKey)
    }
  }, [onClose])

  const handleItemClick = useCallback((item: ContextMenuItem) => {
    if (item.disabled) return
    item.onClick()
    onClose()
  }, [onClose])

  return (
    <div
      ref={ref}
      className={styles.menu}
      style={{ left: pos.x, top: pos.y }}
      onClick={(e) => e.stopPropagation()}
      onContextMenu={(e) => { e.preventDefault(); e.stopPropagation() }}
      role="menu"
    >
      {items.map((item) => (
        <button
          key={item.label}
          type="button"
          className={[
            styles.item,
            item.danger ? styles.danger : '',
            item.disabled ? styles.disabled : '',
          ].filter(Boolean).join(' ')}
          onClick={() => handleItemClick(item)}
          disabled={item.disabled}
          role="menuitem"
        >
          {item.icon && <span className={styles.icon}>{item.icon}</span>}
          <span>{item.label}</span>
        </button>
      ))}
    </div>
  )
}
