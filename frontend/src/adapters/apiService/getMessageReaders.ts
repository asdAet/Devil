import type { AxiosInstance } from "axios";

import type { MessageReadersResult } from "../../domain/interfaces/IApiService";
import { decodeMessageReadersResponse } from "../../dto";
import { resolveRoomId } from "./resolveRoomId";

/**
 * Выполняет API-запрос для загрузки readers конкретного сообщения.
 * @param apiClient Сконфигурированный HTTP-клиент для выполнения запроса.
 * @param roomId Идентификатор комнаты.
 * @param messageId Идентификатор сообщения.
 * @returns Промис с данными, возвращаемыми этой функцией.
 */
export async function getMessageReaders(
  apiClient: AxiosInstance,
  roomId: string,
  messageId: number,
): Promise<MessageReadersResult> {
  const apiRoomRef = await resolveRoomId(apiClient, roomId);
  const encodedRoomRef = encodeURIComponent(apiRoomRef);
  const response = await apiClient.get<unknown>(
    `/chat/rooms/${encodedRoomRef}/messages/${messageId}/readers/`,
  );
  return decodeMessageReadersResponse(response.data);
}
