import { useCallback, useState } from 'react'

import { friendsController } from '../../controllers/FriendsController'
import { useUserProfile } from '../../hooks/useUserProfile'
import { formatLastSeen } from '../../shared/lib/format'
import { Avatar, Spinner } from '../../shared/ui'
import styles from '../../styles/chat/DirectInfoPanel.module.css'

type Props = {
  username: string
}

export function UserProfilePanel({ username }: Props) {
  const { user, loading, error } = useUserProfile(username)
  const [actionStatus, setActionStatus] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const handleAddFriend = useCallback(async () => {
    setBusy(true)
    setActionStatus(null)
    try {
      const result = await friendsController.sendFriendRequest(username)
      setActionStatus(result.status === 'already_friends' ? 'Вы уже друзья' : 'Запрос отправлен')
    } catch {
      setActionStatus('Не удалось отправить запрос')
    } finally {
      setBusy(false)
    }
  }, [username])

  const handleBlock = useCallback(async () => {
    setBusy(true)
    setActionStatus(null)
    try {
      await friendsController.blockUser(username)
      setActionStatus('Пользователь заблокирован')
    } catch {
      setActionStatus('Не удалось заблокировать')
    } finally {
      setBusy(false)
    }
  }, [username])

  if (loading) {
    return (
      <div className={styles.centered}>
        <Spinner size="md" />
      </div>
    )
  }

  if (error || !user) {
    return (
      <div className={styles.centered}>
        <p className={styles.meta}>Пользователь не найден</p>
      </div>
    )
  }

  return (
    <div className={styles.root}>
      <div className={styles.profile}>
        <Avatar
          username={user.username}
          profileImage={user.profileImage}
          avatarCrop={user.avatarCrop}
          size="default"
        />
        <h4 className={styles.peerName}>{user.username}</h4>
        <p className={styles.meta}>
          {formatLastSeen(user.lastSeen ?? null) || 'Был(а) в сети давно'}
        </p>

        <div className={styles.bioSection}>
          <span className={styles.bioLabel}>О себе</span>
          {user.bio ? (
            <p className={styles.bioText}>{user.bio}</p>
          ) : (
            <p className={[styles.bioText, styles.bioEmpty].join(' ')}>Пока ничего не указано.</p>
          )}
        </div>

        {actionStatus && (
          <p className={styles.meta} style={{ marginTop: 8 }}>{actionStatus}</p>
        )}

        <div style={{ display: 'flex', gap: 8, marginTop: 12, width: '100%' }}>
          <button
            type="button"
            style={{
              flex: 1,
              border: 'none',
              borderRadius: 10,
              padding: '10px 14px',
              fontSize: 13,
              background: 'var(--tg-primary, #8774e1)',
              color: '#fff',
              cursor: busy ? 'not-allowed' : 'pointer',
              opacity: busy ? 0.6 : 1,
            }}
            onClick={() => void handleAddFriend()}
            disabled={busy}
          >
            Добавить в друзья
          </button>
          <button
            type="button"
            style={{
              flex: 1,
              border: 'none',
              borderRadius: 10,
              padding: '10px 14px',
              fontSize: 13,
              background: 'rgba(255, 89, 90, 0.15)',
              color: 'var(--tg-danger, #ff595a)',
              cursor: busy ? 'not-allowed' : 'pointer',
              opacity: busy ? 0.6 : 1,
            }}
            onClick={() => void handleBlock()}
            disabled={busy}
          >
            Заблокировать
          </button>
        </div>
      </div>
    </div>
  )
}
