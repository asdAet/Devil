import type { AxiosInstance } from "axios";

import { buildLoginRequestDto, decodeSessionResponse } from "../../dto";
import type { SessionResponse } from "../../domain/interfaces/IApiService";

/**
 * Выполняет логин пользователя.
 * @param apiClient HTTP-клиент.
 * @param identifier Логин или email.
 * @param password Пароль.
 * @returns Декодированное состояние сессии.
 */
export async function login(
  apiClient: AxiosInstance,
  identifier: string,
  password: string,
): Promise<SessionResponse> {
  const body = buildLoginRequestDto({ identifier, password });
  const response = await apiClient.post<unknown>("/auth/login/", body);
  return decodeSessionResponse(response.data);
}
