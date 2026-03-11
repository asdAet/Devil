import { useEffect, useState } from 'react'

import type { AvatarCrop } from '../api/users'
import { avatarFallback } from '../lib/format'
import { AvatarMedia } from './AvatarMedia'

import styles from '../../styles/ui/Avatar.module.css'

type AvatarSize = 'default' | 'small' | 'tiny'

type AvatarProps = {
  username: string
  profileImage?: string | null
  avatarCrop?: AvatarCrop | null
  size?: AvatarSize
  online?: boolean
  className?: string
  loading?: 'eager' | 'lazy'
}

const sizeClassMap: Record<AvatarSize, string> = {
  default: styles.default,
  small: styles.small,
  tiny: styles.tiny,
}

/**
 * Унифицированный аватар пользователя с fallback-инициалами и online-бейджем.
 * @param props Параметры рендера аватара.
 * @returns JSX-блок аватара.
 */
export function Avatar({
  username,
  profileImage = null,
  avatarCrop = null,
  size = 'default',
  online = false,
  className,
  loading = 'lazy',
}: AvatarProps) {
  const [isBroken, setIsBroken] = useState(false)

  useEffect(() => {
    setIsBroken(false)
  }, [profileImage])

  return (
    <div
      className={[
        styles.avatar,
        sizeClassMap[size],
        online ? styles.online : '',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
      data-online={online ? 'true' : 'false'}
      data-size={size}
    >
      {profileImage && !isBroken ? (
        <AvatarMedia
          src={profileImage}
          alt={username}
          avatarCrop={avatarCrop}
          loading={loading}
          decoding="async"
          onError={() => setIsBroken(true)}
        />
      ) : (
        <span>{avatarFallback(username)}</span>
      )}
    </div>
  )
}
