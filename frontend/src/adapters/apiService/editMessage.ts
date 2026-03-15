import type { AxiosInstance } from "axios";

import { decodeEditMessageResponse } from "../../dto";
import type { EditMessageResult } from "../../domain/interfaces/IApiService";
import { resolveRoomApiRef } from "./resolveRoomApiRef";

export async function editMessage(
  apiClient: AxiosInstance,
  roomId: string,
  messageId: number,
  content: string,
): Promise<EditMessageResult> {
  const resolvedRoomId = await resolveRoomApiRef(apiClient, roomId);
  const encodedRoomId = encodeURIComponent(resolvedRoomId);
  const response = await apiClient.patch<unknown>(
    `/chat/rooms/${encodedRoomId}/messages/${messageId}/`,
    { content },
  );
  return decodeEditMessageResponse(response.data);
}
