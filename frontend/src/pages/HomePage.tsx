import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { decodeChatWsEvent } from '../dto'
import type { Message } from '../entities/message/types'
import type { UserProfile } from '../entities/user/types'
import type { ApiError } from '../shared/api/types'
import { useChatActions } from '../hooks/useChatActions'
import { useOnlineStatus } from '../hooks/useOnlineStatus'
import { usePublicRoom } from '../hooks/usePublicRoom'
import { useReconnectingWebSocket } from '../hooks/useReconnectingWebSocket'
import { usePresence } from '../shared/presence'
import { debugLog } from '../shared/lib/debug'
import { sanitizeText } from '../shared/lib/sanitize'
import { getWebSocketBase } from '../shared/lib/ws'
import { Avatar, Button, Card, Toast } from '../shared/ui'
import styles from '../styles/pages/HomePage.module.css'

type Props = {
  user: UserProfile | null
  onNavigate: (path: string) => void
}

const buildTempId = (seed: number) => Date.now() * 1000 + seed
const TEXT_GUESTS_ONLINE = 'Гостей онлайн'
const TEXT_PROMPT_LOGIN_ONLINE = 'Войдите, чтобы видеть участников онлайн.'
const TEXT_LOADING_ONLINE = 'Загружаем список онлайн...'
const TEXT_OPEN_PROFILE_PREFIX = 'Открыть профиль пользователя'

export function HomePage({ user, onNavigate }: Props) {
  const { publicRoom, loading } = usePublicRoom(user)
  const { getRoomDetails, getRoomMessages } = useChatActions()
  const isOnline = useOnlineStatus()
  const [liveMessages, setLiveMessages] = useState<Message[]>([])
  const [creatingRoom, setCreatingRoom] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)
  const tempIdRef = useRef(0)
  const { online, guests, status } = usePresence()

  const visiblePublicRoom = useMemo(() => publicRoom, [publicRoom])
  const publicRoomLabel = visiblePublicRoom?.name || 'Публичная комната'
  const presenceLoading = Boolean(user && status !== 'online')
  const onlineUsernames = useMemo(
    () => new Set(status === 'online' ? online.map((entry) => entry.username) : []),
    [online, status],
  )

  const openUserProfile = useCallback(
    (username: string) => {
      if (!username) return
      onNavigate(`/users/${encodeURIComponent(username)}`)
    },
    [onNavigate],
  )

  useEffect(() => {
    let active = true

    if (!visiblePublicRoom) {
      queueMicrotask(() => {
        if (active) setLiveMessages([])
      })
      return () => {
        active = false
      }
    }

    getRoomMessages(visiblePublicRoom.slug, { limit: 4 })
      .then((payload) => {
        if (!active) return
        const sanitized = payload.messages.map((msg) => ({
          ...msg,
          content: sanitizeText(msg.content, 200),
        }))
        setLiveMessages(sanitized.slice(-4))
      })
      .catch((err) => debugLog('Live feed history failed', err))

    return () => {
      active = false
    }
  }, [visiblePublicRoom, getRoomMessages])

  const liveUrl = useMemo(() => {
    if (!visiblePublicRoom) return null
    return `${getWebSocketBase()}/ws/chat/${encodeURIComponent(visiblePublicRoom.slug)}/`
  }, [visiblePublicRoom])

  const handleLiveMessage = useCallback((event: MessageEvent) => {
    const decoded = decodeChatWsEvent(event.data)
    if (decoded.type !== 'chat_message') {
      return
    }

    try {
      tempIdRef.current += 1
      const next: Message = {
        id: buildTempId(tempIdRef.current),
        username: decoded.message.username,
        content: sanitizeText(decoded.message.content, 200),
        profilePic: decoded.message.profilePic || null,
        createdAt: new Date().toISOString(),
      }
      setLiveMessages((prev) => [...prev, next].slice(-4))
    } catch (error) {
      debugLog('Live feed WS parse failed', error)
    }
  }, [])

  useReconnectingWebSocket({
    url: liveUrl,
    onMessage: handleLiveMessage,
    onError: (err) => debugLog('Live feed WS error', err),
  })

  const createRoomSlug = useCallback((length = 12) => {
    if (globalThis.crypto?.randomUUID) {
      return globalThis.crypto.randomUUID().replace(/-/g, '').slice(0, length)
    }

    const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    const values = new Uint8Array(length)
    if (globalThis.crypto?.getRandomValues) {
      globalThis.crypto.getRandomValues(values)
      return Array.from(values, (value) => alphabet[value % alphabet.length]).join('')
    }

    let fallback = ''
    for (let index = 0; index < length; index += 1) {
      fallback += alphabet[Math.floor(Math.random() * alphabet.length)]
    }
    return fallback
  }, [])

  const onCreateRoom = useCallback(async () => {
    if (!user || creatingRoom) return

    setCreateError(null)
    setCreatingRoom(true)
    let navigated = false

    try {
      const maxAttempts = 3
      for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
        const slug = createRoomSlug()
        try {
          const details = await getRoomDetails(slug)
          if (details.created === false) {
            continue
          }
          navigated = true
          onNavigate(`/rooms/${encodeURIComponent(slug)}`)
          return
        } catch (err) {
          const apiErr = err as ApiError
          if (apiErr && typeof apiErr.status === 'number' && apiErr.status === 409) {
            continue
          }
          throw err
        }
      }
      setCreateError('Не удалось создать уникальную комнату. Попробуйте еще раз.')
    } catch (err) {
      debugLog('Room create failed', err)
      setCreateError('Не удалось создать комнату. Попробуйте еще раз.')
    } finally {
      if (!navigated) {
        setCreatingRoom(false)
      }
    }
  }, [user, creatingRoom, createRoomSlug, getRoomDetails, onNavigate])

  const openPublicRoom = useCallback(() => {
    const slug = visiblePublicRoom?.slug || 'public'
    onNavigate(`/rooms/${encodeURIComponent(slug)}`)
  }, [onNavigate, visiblePublicRoom])

  return (
    <div className={styles.stack}>
      {!isOnline && (
        <Toast variant="warning" role="status">
          Нет подключения к интернету. Мы восстановим соединение автоматически.
        </Toast>
      )}

      <section className={styles.hero}>
        <div className={styles.heroContent}>
          <p className={styles.eyebrow}>EchoChat</p>
          <h1 className={styles.heroTitle}>Командный чат по комнатам в реальном времени.</h1>
          <p className={styles.lead}>
            Публичная комната для общего общения, приватные комнаты для ваших задач и личные диалоги 1:1.
            Сообщения приходят мгновенно.
          </p>
          <ul className={styles.heroBullets}>
            <li>Общий публичный эфир</li>
            <li>Приватные комнаты для авторизованных пользователей</li>
            <li>Онлайн-статус и быстрый переход в профиль</li>
          </ul>
          <div className={styles.actions}>
            <Button variant="outline" onClick={openPublicRoom} disabled={loading || !visiblePublicRoom}>
              Открыть публичную комнату
            </Button>
            {!user && (
              <Button variant="ghost" onClick={() => onNavigate('/register')}>
                Создать аккаунт
              </Button>
            )}
          </div>
        </div>

        <Card className={styles.heroCard}>
          <div className={styles.heroCardHeader}>
            <div>
              <p className={styles.eyebrow}>Сейчас в эфире</p>
              <h2>{publicRoomLabel}</h2>
            </div>
            <span
              className={[
                styles.statusPill,
                visiblePublicRoom ? styles.statusLive : styles.statusLoading,
              ]
                .filter(Boolean)
                .join(' ')}
            >
              {visiblePublicRoom ? 'онлайн' : 'загрузка'}
            </span>
          </div>

          {visiblePublicRoom ? (
            <div className={styles.liveFeed} aria-live="polite">
              {liveMessages.map((msg) => (
                <div className={styles.liveItem} key={`${msg.id}-${msg.createdAt}`}>
                  <span className={styles.liveUser}>{msg.username}</span>
                  <span className={styles.liveText}>{msg.content}</span>
                </div>
              ))}
              {!liveMessages.length && <p className={styles.muted}>Пока нет сообщений. Начните обсуждение первыми.</p>}
            </div>
          ) : (
            <p className={styles.muted}>Подключаемся к публичной комнате...</p>
          )}
        </Card>
      </section>

      <section className={styles.grid}>
        <Card className={styles.sectionCard}>
          <div className={styles.cardHeader}>
            <div>
              <p className={styles.eyebrow}>Приватная комната</p>
              <h3>Создать новую</h3>
            </div>
          </div>

          <p className={styles.muted}>
            Авторизованные пользователи могут создать приватную комнату с уникальным slug.
          </p>

          <div className={styles.form}>
            <Button variant="primary" onClick={onCreateRoom} disabled={!user || creatingRoom || !isOnline}>
              {creatingRoom ? 'Создаем комнату...' : 'Создать приватную комнату'}
            </Button>
            {createError && <p className={styles.note}>{createError}</p>}
            {!user && <p className={styles.note}>Войдите, чтобы создавать приватные комнаты.</p>}
            {!isOnline && <p className={styles.note}>Нет сети. Создание комнаты временно недоступно.</p>}
          </div>
        </Card>

        <Card className={styles.sectionCard}>
          <div className={styles.cardHeader}>
            <div>
              <p className={styles.eyebrow}>Публичная комната</p>
              <h3>{publicRoomLabel}</h3>
            </div>
            <span className={styles.statusPill}>{loading ? 'загрузка' : 'готово'}</span>
          </div>

          <p className={styles.muted}>
            Общий поток сообщений для новостей, объявлений и открытых обсуждений.
          </p>

          <Button variant="outline" onClick={openPublicRoom} disabled={!visiblePublicRoom || loading}>
            Перейти в публичную комнату
          </Button>
        </Card>

        <Card className={styles.sectionCard}>
          <div className={styles.cardHeader}>
            <div>
              <p className={styles.eyebrow}>{TEXT_GUESTS_ONLINE}</p>
            </div>
            <span className={styles.statusPill}>{guests}</span>
          </div>

          <div className={styles.cardHeader}>
            <div>
              <p className={styles.eyebrow}>Кто онлайн</p>
            </div>
            <span className={styles.statusPill}>{user ? (presenceLoading ? '...' : online.length) : '-'}</span>
          </div>

          {!user ? (
            <p className={styles.muted}>{TEXT_PROMPT_LOGIN_ONLINE}</p>
          ) : presenceLoading ? (
            <p className={styles.muted}>{TEXT_LOADING_ONLINE}</p>
          ) : online.length ? (
            <div className={styles.onlineList}>
              {online.map((entry) => (
                <div className={styles.onlineItem} key={entry.username}>
                  <button
                    type="button"
                    className={styles.avatarLink}
                    aria-label={`${TEXT_OPEN_PROFILE_PREFIX} ${entry.username}`}
                    onClick={() => openUserProfile(entry.username)}
                  >
                    <Avatar
                      username={entry.username}
                      profileImage={entry.profileImage}
                      size="tiny"
                      online={onlineUsernames.has(entry.username)}
                    />
                  </button>
                  <span>{entry.username}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className={styles.muted}>Пока никого нет в сети.</p>
          )}
        </Card>
      </section>
    </div>
  )
}
