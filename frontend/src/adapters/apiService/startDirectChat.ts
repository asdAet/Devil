import type { AxiosInstance } from "axios";

import type { DirectStartResponse } from "../../domain/interfaces/IApiService";
import { decodeDirectStartResponse } from "../../dto";

/**
 * Создает или возвращает direct-чат по публичному ref.
 * @param apiClient HTTP-клиент.
 * @param publicRef Публичный handle/public_id собеседника.
 * @returns Нормализованные данные direct-комнаты.
 */
export const startDirectChat = async (
  apiClient: AxiosInstance,
  publicRef: string,
): Promise<DirectStartResponse> => {
  const response = await apiClient.post<unknown>("/chat/direct/start/", {
    ref: publicRef,
  });
  return decodeDirectStartResponse(response.data);
};
