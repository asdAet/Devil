import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useInfoPanel } from '../../shared/layout/useInfoPanel'
import { ChatSearch } from '../chat/ChatSearch'
import { DirectInfoPanel } from '../chat/DirectInfoPanel'
import { UserProfilePanel } from '../chat/UserProfilePanel'
import { GroupInfoPanel } from '../groups/GroupInfoPanel'
import styles from '../../styles/layout/InfoPanel.module.css'

const TITLES: Record<string, string> = {
  profile: 'Профиль',
  group: 'Информация',
  search: 'Поиск',
  direct: 'Контакт и вложения',
}

function PanelContent({
  content,
  targetId,
  currentUsername,
  onJumpToMessage,
}: {
  content: string
  targetId: string | null
  currentUsername: string | null
  onJumpToMessage: (slug: string, messageId: number) => void
}) {
  if (content === 'search' && targetId) {
    return <ChatSearch slug={targetId} onResultClick={(messageId) => onJumpToMessage(targetId, messageId)} />
  }

  if (content === 'group' && targetId) {
    return <GroupInfoPanel slug={targetId} currentUsername={currentUsername} />
  }

  if (content === 'direct' && targetId) {
    return <DirectInfoPanel slug={targetId} />
  }

  if (content === 'profile' && targetId) {
    return <UserProfilePanel username={targetId} />
  }

  return (
    <div className={styles.placeholder}>
      <p>Выберите контент для отображения</p>
    </div>
  )
}

export function InfoPanel({ currentUsername }: { currentUsername: string | null }) {
  const { isOpen, content, targetId, close } = useInfoPanel()
  const navigate = useNavigate()
  const [rendered, setRendered] = useState(false)
  const [renderContent, setRenderContent] = useState<string | null>(null)
  const [renderTargetId, setRenderTargetId] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen && content) {
      setRendered(true)
      setRenderContent(content)
      setRenderTargetId(targetId ?? null)
      return
    }

    if (!isOpen) {
      const timer = window.setTimeout(() => {
        setRendered(false)
        setRenderContent(null)
        setRenderTargetId(null)
      }, 220)
      return () => window.clearTimeout(timer)
    }
  }, [isOpen, content, targetId])

  const onJumpToMessage = (slug: string, messageId: number) => {
    navigate(`/rooms/${encodeURIComponent(slug)}?message=${messageId}`)
  }

  if (!rendered || !renderContent) return null

  const compactHeader = renderContent === 'group'

  return (
    <>
      <div
        className={[styles.overlay, !isOpen ? styles.overlayHidden : ''].filter(Boolean).join(' ')}
        onClick={close}
        aria-hidden="true"
      />
      <aside
        className={[styles.panel, !isOpen ? styles.panelHidden : ''].filter(Boolean).join(' ')}
        aria-label="Информационная панель"
      >
        <div className={styles.header}>
          <h3 className={styles.headerTitle}>{TITLES[renderContent] ?? 'Информация'}</h3>
          <button
            type="button"
            className={styles.closeBtn}
            onClick={close}
            aria-label="Закрыть панель"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>
        <div className={[styles.body, compactHeader ? styles.bodyCompact : ''].filter(Boolean).join(' ')}>
          <PanelContent
            content={renderContent}
            targetId={renderTargetId}
            currentUsername={currentUsername}
            onJumpToMessage={onJumpToMessage}
          />
        </div>
      </aside>
    </>
  )
}
