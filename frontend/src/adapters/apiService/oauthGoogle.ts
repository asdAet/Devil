import type { AxiosInstance } from "axios";

import { buildOAuthGoogleRequestDto, decodeSessionResponse } from "../../dto";
import type { SessionResponse } from "../../domain/interfaces/IApiService";

/**
 * Выполняет вход/регистрацию через Google OAuth.
 * @param apiClient HTTP-клиент.
 * @param token OAuth token от Google Identity Services.
 * @param tokenType Тип токена (`idToken` или `accessToken`).
 * @returns Декодированное состояние сессии.
 */
export async function oauthGoogle(
  apiClient: AxiosInstance,
  token: string,
  tokenType: "idToken" | "accessToken" = "idToken",
  username?: string,
): Promise<SessionResponse> {
  const normalizedToken = token.trim();
  const body = buildOAuthGoogleRequestDto(
    tokenType === "accessToken"
      ? { accessToken: normalizedToken, username }
      : { idToken: normalizedToken, username },
  );

  const response = await apiClient.post<unknown>("/auth/oauth/google/", body);
  return decodeSessionResponse(response.data);
}
