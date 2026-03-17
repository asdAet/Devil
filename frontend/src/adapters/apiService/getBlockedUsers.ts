import type { AxiosInstance } from "axios";

import { decodeBlockedListResponse } from "../../dto/http/friends";
import type { BlockedUser } from "../../entities/friend/types";

export async function getBlockedUsers(
  apiClient: AxiosInstance,
): Promise<BlockedUser[]> {
  const response = await apiClient.get("/friends/blocked/");
  return decodeBlockedListResponse(response.data);
}
