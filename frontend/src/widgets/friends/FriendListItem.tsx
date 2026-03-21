import type { Friend } from "../../entities/friend/types";
import { resolveIdentityLabel } from "../../shared/lib/userIdentity";
import { Avatar, Dropdown } from "../../shared/ui";
import styles from "../../styles/friends/FriendListItem.module.css";

/**
 * Описывает входные props компонента `Props`.
 */
type Props = {
  friend: Friend;
  isOnline: boolean;
  onMessage: (publicRef: string) => void;
  onRemove: (userId: number) => void;
  onBlock: (publicRef: string) => void;
};

const IconMore = () => (
  <svg
    width="18"
    height="18"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
  >
    <circle cx="12" cy="5" r="1.5" fill="currentColor" stroke="none" />
    <circle cx="12" cy="12" r="1.5" fill="currentColor" stroke="none" />
    <circle cx="12" cy="19" r="1.5" fill="currentColor" stroke="none" />
  </svg>
);

/**
 * Компонент FriendListItem рендерит UI текущего раздела и связывает действия пользователя с обработчиками.
 *
 * @param props Свойства компонента.
 */
export function FriendListItem({
  friend,
  isOnline,
  onMessage,
  onRemove,
  onBlock,
}: Props) {
  const peerRef = friend.publicRef;
  const displayName = resolveIdentityLabel(friend);

  return (
    <div className={styles.item}>
      <Avatar
        username={displayName}
        profileImage={friend.profileImage}
        avatarCrop={friend.avatarCrop ?? undefined}
        size="small"
        online={isOnline}
        loading="eager"
      />
      <div className={styles.itemInfo}>
        <div className={styles.itemName}>{displayName}</div>
        <div className={styles.itemMeta}>{isOnline ? "В сети" : "Не в сети"}</div>
      </div>
      <div className={styles.itemActions}>
        <Dropdown
          align="right"
          wrapperClassName={styles.actionMenuWrap}
          menuClassName={styles.actionMenu}
          trigger={
            <button
              type="button"
              className={styles.actionMenuTrigger}
              aria-label={`Действия для ${displayName}`}
            >
              <IconMore />
            </button>
          }
        >
          <button
            type="button"
            className={styles.actionMenuItem}
            onClick={() => onMessage(peerRef)}
          >
            Написать
          </button>
          <button
            type="button"
            className={[styles.actionMenuItem, styles.actionMenuItemDanger].join(" ")}
            onClick={() => onRemove(friend.userId)}
          >
            Удалить
          </button>
          <button
            type="button"
            className={[styles.actionMenuItem, styles.actionMenuItemDanger].join(" ")}
            onClick={() => onBlock(peerRef)}
          >
            Блок
          </button>
        </Dropdown>
      </div>
    </div>
  );
}
