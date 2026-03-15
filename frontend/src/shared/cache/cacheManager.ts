import { encodeSwCacheMessage, type SwCacheMessage } from "../../dto";

const postMessage = (message: SwCacheMessage): void => {
  if (typeof navigator === "undefined") return;
  if (!navigator.serviceWorker) return;

  const payload = encodeSwCacheMessage(message);
  const controller = navigator.serviceWorker.controller;
  if (controller) {
    controller.postMessage(payload);
    return;
  }

  navigator.serviceWorker.ready
    .then((registration) => {
      registration.active?.postMessage(payload);
    })
    .catch(() => {});
};

/**
 * Инвалидирует кэш сообщений комнаты.
 * @param roomRef Room ref (обычно roomId).
 */
export const invalidateRoomMessages = (roomRef: string) => {
  if (!roomRef) return;
  postMessage({ type: "invalidate", key: "roomMessages", roomRef });
};

/**
 * Инвалидирует кэш деталей комнаты.
 * @param roomRef Room ref (обычно roomId).
 */
export const invalidateRoomDetails = (roomRef: string) => {
  if (!roomRef) return;
  postMessage({ type: "invalidate", key: "roomDetails", roomRef });
};

/**
 * Инвалидирует кэш списка direct-чатов.
 */
export const invalidateDirectChats = () => {
  postMessage({ type: "invalidate", key: "directChats" });
};

/**
 * Инвалидирует кэш публичного профиля пользователя.
 * @param publicRef Публичный ref пользователя (handle или fallback-id).
 */
export const invalidateUserProfile = (publicRef: string) => {
  if (!publicRef) return;
  postMessage({ type: "invalidate", key: "userProfile", publicRef });
};

/**
 * Инвалидирует кэш собственного профиля.
 */
export const invalidateSelfProfile = () => {
  postMessage({ type: "invalidate", key: "selfProfile" });
};

/**
 * Очищает все пользовательские API-кэши.
 */
export const clearAllUserCaches = () => {
  postMessage({ type: "clearUserCaches" });
};
