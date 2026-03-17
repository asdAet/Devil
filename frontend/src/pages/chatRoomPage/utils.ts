import type { Message } from "../../entities/message/types";
import type { UserProfile } from "../../entities/user/types";
import { normalizeAvatarCrop } from "../../shared/lib/avatarCrop";
import { formatDayLabel } from "../../shared/lib/format";

export type InitialPositioningPhase = "pending" | "positioning" | "settled";
export type InitialPositioningTarget = "unread" | "bottom";

export type ReadReceipt = {
  userId: number;
  publicRef: string;
  username: string;
  displayName?: string;
  lastReadMessageId: number;
};

export type UnreadDividerRenderTarget = {
  messageId: number | null;
  insertAtTop: boolean;
};

export type TimelineItem =
  | { type: "day"; key: string; label: string }
  | { type: "message"; message: Message }
  | { type: "unread" };

const PENDING_READ_STORAGE_PREFIX = "chat.pendingRead.";
const CSRF_SESSION_STORAGE_KEY = "csrfToken";

export const TYPING_TIMEOUT_MS = 5_000;
export const MAX_HISTORY_JUMP_ATTEMPTS = 60;
export const MAX_HISTORY_NO_PROGRESS_ATTEMPTS = 2;
export const MARK_READ_DEBOUNCE_MS = 180;

export const normalizeActorRef = (value: string | null | undefined): string => {
  if (!value) return "";
  const normalized = value.trim().toLowerCase();
  if (!normalized) return "";
  return normalized.startsWith("@") ? normalized.slice(1) : normalized;
};

export const resolveCurrentActorRef = (user: UserProfile | null): string => {
  if (!user) return "";
  return (
    normalizeActorRef(user.publicRef) ||
    normalizeActorRef(user.username) ||
    normalizeActorRef(user.publicId) ||
    ""
  );
};

export const resolveMessageActorRef = (
  message: Pick<Message, "publicRef">,
): string => normalizeActorRef(message.publicRef);

export const isOwnMessage = (message: Message, currentActorRef: string) =>
  Boolean(
    currentActorRef && resolveMessageActorRef(message) === currentActorRef,
  );

export const normalizeReadMessageId = (value: unknown): number => {
  if (typeof value === "number" && Number.isFinite(value))
    return Math.max(0, Math.trunc(value));
  if (typeof value === "string" && value.trim()) {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) return Math.max(0, Math.trunc(parsed));
  }
  return 0;
};

export const parseRoomIdRef = (value: unknown): number | null => {
  if (typeof value === "number") {
    if (!Number.isFinite(value) || value <= 0) return null;
    return Math.trunc(value);
  }
  if (typeof value !== "string") return null;
  const normalized = value.trim();
  if (!/^\d+$/.test(normalized)) return null;
  const parsed = Number(normalized);
  if (!Number.isFinite(parsed) || parsed <= 0) return null;
  return Math.trunc(parsed);
};

export const isFileDragPayload = (
  dataTransfer: DataTransfer | null | undefined,
): boolean => {
  if (!dataTransfer) return false;
  if (dataTransfer.files && dataTransfer.files.length > 0) return true;

  const transferTypes = dataTransfer.types;
  if (!transferTypes) return false;

  if (
    "contains" in transferTypes &&
    typeof transferTypes.contains === "function"
  ) {
    return transferTypes.contains("Files");
  }

  return Array.from(transferTypes).includes("Files");
};

const pendingReadStorageKey = (roomSlug: string) =>
  `${PENDING_READ_STORAGE_PREFIX}${roomSlug}`;

export const readPendingReadFromStorage = (roomSlug: string): number => {
  if (typeof window === "undefined") return 0;
  try {
    return normalizeReadMessageId(
      window.sessionStorage.getItem(pendingReadStorageKey(roomSlug)),
    );
  } catch {
    return 0;
  }
};

export const writePendingReadToStorage = (
  roomSlug: string,
  lastReadMessageId: number,
): void => {
  if (typeof window === "undefined") return;
  try {
    const normalized = normalizeReadMessageId(lastReadMessageId);
    if (normalized < 1) {
      window.sessionStorage.removeItem(pendingReadStorageKey(roomSlug));
      return;
    }
    window.sessionStorage.setItem(
      pendingReadStorageKey(roomSlug),
      String(normalized),
    );
  } catch {
    // Storage can be unavailable in private mode or restricted contexts.
  }
};

export const clearPendingReadFromStorage = (roomSlug: string): void => {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.removeItem(pendingReadStorageKey(roomSlug));
  } catch {
    // noop
  }
};

const readCookieValue = (cookie: string, name: string): string | null => {
  const chunks = cookie.split(";").map((entry) => entry.trim());
  const match = chunks.find((entry) => entry.startsWith(`${name}=`));
  if (!match) return null;
  const value = match.slice(name.length + 1).trim();
  return value || null;
};

export const resolveCsrfToken = (): string | null => {
  if (
    typeof document !== "undefined" &&
    typeof document.cookie === "string" &&
    document.cookie.length > 0
  ) {
    const fromCookie = readCookieValue(document.cookie, "csrftoken");
    if (fromCookie) return fromCookie;
  }

  if (typeof window !== "undefined") {
    try {
      const fromStorage = window.sessionStorage.getItem(
        CSRF_SESSION_STORAGE_KEY,
      );
      if (fromStorage && fromStorage.trim()) return fromStorage.trim();
    } catch {
      // noop
    }
  }

  return null;
};

export const extractApiErrorMessage = (error: unknown, fallback: string) => {
  if (!error || typeof error !== "object") return fallback;
  const candidate = error as {
    message?: string;
    data?: {
      error?: string;
      detail?: string;
      code?: string;
      details?: {
        maxPerMessage?: number;
        maxSize?: number;
        allowedTypes?: string[];
      };
    };
  };
  const code = candidate.data?.code;
  const details = candidate.data?.details;
  if (code === "no_files") {
    return "Файлы не переданы. Выберите вложение и повторите отправку.";
  }
  if (code === "too_many_files") {
    const maxPerMessage = details?.maxPerMessage;
    return typeof maxPerMessage === "number"
      ? `Слишком много файлов. Максимум ${maxPerMessage} на сообщение.`
      : "Слишком много файлов в одном сообщении.";
  }
  if (code === "file_too_large") {
    const maxSize = details?.maxSize;
    if (typeof maxSize === "number" && maxSize > 0) {
      const maxMb = Math.ceil(maxSize / (1024 * 1024));
      return `Файл превышает лимит размера (${maxMb} МБ).`;
    }
    return "Файл превышает максимально допустимый размер.";
  }
  if (code === "unsupported_type") {
    if (
      Array.isArray(details?.allowedTypes) &&
      details.allowedTypes.length > 0
    ) {
      return `Тип файла не поддерживается. Разрешены: ${details.allowedTypes.join(", ")}.`;
    }
    return "Тип файла не поддерживается.";
  }
  if (code === "invalid_reply_to") {
    return "Сообщение для ответа недоступно. Обновите чат и попробуйте снова.";
  }
  if (candidate.data?.error) return candidate.data.error;
  if (candidate.data?.detail) return candidate.data.detail;
  if (candidate.message && !candidate.message.includes("status code"))
    return candidate.message;
  return fallback;
};

export const sameAvatarCrop = (
  left: Message["avatarCrop"],
  right: Message["avatarCrop"],
) => {
  const normalizedLeft = normalizeAvatarCrop(left ?? null);
  const normalizedRight = normalizeAvatarCrop(right ?? null);
  if (!normalizedLeft && !normalizedRight) return true;
  if (!normalizedLeft || !normalizedRight) return false;
  return (
    normalizedLeft.x === normalizedRight.x &&
    normalizedLeft.y === normalizedRight.y &&
    normalizedLeft.width === normalizedRight.width &&
    normalizedLeft.height === normalizedRight.height
  );
};

export const formatGroupTypingLabel = (
  kind: string | null | undefined,
  activeTypingUsers: string[],
): string | null => {
  if (kind !== "group" || activeTypingUsers.length === 0) return null;
  if (activeTypingUsers.length === 1)
    return `${activeTypingUsers[0]} печатает...`;
  if (activeTypingUsers.length === 2)
    return `${activeTypingUsers[0]} и ${activeTypingUsers[1]} печатают...`;
  return `${activeTypingUsers[0]} и ещё ${activeTypingUsers.length - 1} печатают...`;
};

export const buildTimeline = (
  messages: Message[],
  unreadDividerRenderTarget: UnreadDividerRenderTarget,
): TimelineItem[] => {
  const items: TimelineItem[] = [];
  const nowDate = new Date();
  let lastKey: string | null = null;
  let unreadInserted = false;
  const unreadDividerId = unreadDividerRenderTarget.messageId;

  if (unreadDividerRenderTarget.insertAtTop) {
    items.push({ type: "unread" });
    unreadInserted = true;
  }

  for (const msg of messages) {
    if (!unreadInserted && unreadDividerId && msg.id === unreadDividerId) {
      items.push({ type: "unread" });
      unreadInserted = true;
    }
    const date = new Date(msg.createdAt);
    if (!Number.isNaN(date.getTime())) {
      const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
      if (key !== lastKey) {
        const label = formatDayLabel(date, nowDate);
        if (label) {
          items.push({ type: "day", key, label });
          lastKey = key;
        }
      }
    }
    items.push({ type: "message", message: msg });
  }

  return items;
};
