import type { AxiosInstance } from "axios";

import { decodeSearchResponse } from "../../dto";
import type { SearchResult } from "../../domain/interfaces/IApiService";
import { resolveRoomApiRef } from "./resolveRoomApiRef";

export async function searchMessages(
  apiClient: AxiosInstance,
  roomId: string,
  query: string,
): Promise<SearchResult> {
  const apiRoomRef = await resolveRoomApiRef(apiClient, roomId);
  const encodedRoomRef = encodeURIComponent(apiRoomRef);
  const response = await apiClient.get<unknown>(
    `/chat/rooms/${encodedRoomRef}/messages/search/?q=${encodeURIComponent(query)}`,
  );
  return decodeSearchResponse(response.data);
}
