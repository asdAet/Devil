import type { AxiosInstance } from "axios";
import { resolveRoomApiRef } from "./resolveRoomApiRef";

export async function deleteMessage(
  apiClient: AxiosInstance,
  roomId: string,
  messageId: number,
): Promise<void> {
  const apiRoomRef = await resolveRoomApiRef(apiClient, roomId);
  const encodedRoomRef = encodeURIComponent(apiRoomRef);
  await apiClient.delete(`/chat/rooms/${encodedRoomRef}/messages/${messageId}/`);
}
