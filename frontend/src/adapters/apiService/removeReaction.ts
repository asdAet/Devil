import type { AxiosInstance } from "axios";
import { resolveRoomApiRef } from "./resolveRoomApiRef";

export async function removeReaction(
  apiClient: AxiosInstance,
  roomId: string,
  messageId: number,
  emoji: string,
): Promise<void> {
  const apiRoomRef = await resolveRoomApiRef(apiClient, roomId);
  const encodedRoomRef = encodeURIComponent(apiRoomRef);
  await apiClient.delete(
    `/chat/rooms/${encodedRoomRef}/messages/${messageId}/reactions/${encodeURIComponent(emoji)}/`,
  );
}
