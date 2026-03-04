import type { AvatarCrop } from '../../shared/api/users'

export type Message = {
  id: number
  username: string
  content: string
  profilePic: string | null
  avatarCrop?: AvatarCrop | null
  createdAt: string
}
