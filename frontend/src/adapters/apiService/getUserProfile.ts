import type { AxiosInstance } from "axios";

import { decodeProfileEnvelopeResponse } from "../../dto";
import type { UserProfile } from "../../entities/user/types";

/**
 * Загружает публичный профиль пользователя.
 * @param apiClient HTTP-клиент.
 * @param ref Публичный ref пользователя (handle/fallback-id).
 * @returns Нормализованный профиль пользователя.
 */
export async function getUserProfile(
  apiClient: AxiosInstance,
  ref: string,
): Promise<{ user: UserProfile }> {
  const safe = encodeURIComponent(ref);
  const response = await apiClient.get<unknown>(`/public/resolve/${safe}`);
  const payload =
    typeof response.data === "object" && response.data !== null
      ? (response.data as Record<string, unknown>)
      : {};
  return decodeProfileEnvelopeResponse({ user: payload.user });
}
