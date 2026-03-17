import type { AxiosInstance } from "axios";

import type { SessionResponse } from "../../domain/interfaces/IApiService";
import { buildRegisterRequestDto, decodeSessionResponse } from "../../dto";

/**
 * Выполняет регистрацию пользователя.
 * @param apiClient HTTP-клиент.
 * @param login Логин.
 * @param password Пароль.
 * @param passwordConfirm Повтор пароля.
 * @returns Декодированное состояние сессии.
 */
export async function register(
  apiClient: AxiosInstance,
  login: string,
  password: string,
  passwordConfirm: string,
  name: string,
  username?: string,
  email?: string,
): Promise<SessionResponse> {
  const body = buildRegisterRequestDto({
    login,
    password,
    passwordConfirm,
    name,
    username,
    email,
  });
  const response = await apiClient.post<unknown>("/auth/register/", body);
  return decodeSessionResponse(response.data);
}
