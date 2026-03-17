import type { AxiosInstance } from "axios";

import type { ReactionResult } from "../../domain/interfaces/IApiService";
import { decodeReactionResponse } from "../../dto";
import { resolveRoomId } from "./resolveRoomId";

export async function addReaction(
  apiClient: AxiosInstance,
  roomId: string,
  messageId: number,
  emoji: string,
): Promise<ReactionResult> {
  const apiRoomRef = await resolveRoomId(apiClient, roomId);
  const encodedRoomRef = encodeURIComponent(apiRoomRef);
  const response = await apiClient.post<unknown>(
    `/chat/rooms/${encodedRoomRef}/messages/${messageId}/reactions/`,
    { emoji },
  );
  return decodeReactionResponse(response.data);
}
