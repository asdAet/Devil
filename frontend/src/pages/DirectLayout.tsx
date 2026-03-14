import type { UserProfile } from "../entities/user/types";
import { Panel } from "../shared/ui";
import styles from "../styles/pages/DirectLayout.module.css";
import { DirectChatByUsernamePage } from "./DirectChatByUsernamePage";

type Props = {
  user: UserProfile | null;
  publicRef?: string;
  onNavigate: (path: string) => void;
};

/**
 * Direct chat layout: conversation list is shown in the global sidebar,
 * this page only renders the active DM thread.
 */
export function DirectLayout({ user, publicRef, onNavigate }: Props) {
  const hasActive = Boolean(publicRef);

  return (
    <div
      className={[styles.directLayout, hasActive ? styles.chatMode : ""]
        .filter(Boolean)
        .join(" ")}
    >
      <section className={styles.main}>
        {hasActive && publicRef ? (
          <DirectChatByUsernamePage
            key={publicRef}
            user={user}
            publicRef={publicRef}
            onNavigate={onNavigate}
          />
        ) : (
          <Panel muted>
            Выберите диалог в боковой панели, чтобы начать чат.
          </Panel>
        )}
      </section>
    </div>
  );
}
