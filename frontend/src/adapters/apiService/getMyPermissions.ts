import type { AxiosInstance } from "axios";

import { decodeMyPermissionsResponse } from "../../dto";
import type { MyPermissions } from "../../entities/role/types";
import { resolveRoomApiRef } from "./resolveRoomApiRef";

export async function getMyPermissions(
  apiClient: AxiosInstance,
  slug: string,
): Promise<MyPermissions> {
  const roomRef = await resolveRoomApiRef(apiClient, slug);
  const response = await apiClient.get<unknown>(
    `/chat/rooms/${encodeURIComponent(roomRef)}/permissions/me/`,
  );
  return decodeMyPermissionsResponse(response.data);
}
