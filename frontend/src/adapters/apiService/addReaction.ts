import type { AxiosInstance } from "axios";

import { decodeReactionResponse } from "../../dto";
import type { ReactionResult } from "../../domain/interfaces/IApiService";
import { resolveRoomApiRef } from "./resolveRoomApiRef";

export async function addReaction(
  apiClient: AxiosInstance,
  roomId: string,
  messageId: number,
  emoji: string,
): Promise<ReactionResult> {
  const apiRoomRef = await resolveRoomApiRef(apiClient, roomId);
  const encodedRoomRef = encodeURIComponent(apiRoomRef);
  const response = await apiClient.post<unknown>(
    `/chat/rooms/${encodedRoomRef}/messages/${messageId}/reactions/`,
    { emoji },
  );
  return decodeReactionResponse(response.data);
}
