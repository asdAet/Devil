const GOOGLE_IDENTITY_SCRIPT_ID = "google-identity-services";
const GOOGLE_IDENTITY_SCRIPT_SRC = "https://accounts.google.com/gsi/client";
const GOOGLE_OAUTH_SCOPE = "openid email profile";
const GOOGLE_PROMPT_TIMEOUT_MS = 25_000;

type GoogleCredentialResponse = {
  credential?: string;
  select_by?: string;
};

type GoogleIdClientConfig = {
  client_id: string;
  callback: (response: GoogleCredentialResponse) => void;
  cancel_on_tap_outside?: boolean;
  auto_select?: boolean;
  use_fedcm_for_prompt?: boolean;
  itp_support?: boolean;
};

type GoogleTokenResponse = {
  access_token?: string;
  error?: string;
  error_description?: string;
};

type GoogleTokenErrorResponse = {
  type?: string;
};

type GoogleTokenClient = {
  requestAccessToken: (overrideConfig?: { prompt?: string }) => void;
};

type GoogleTokenClientConfig = {
  client_id: string;
  scope: string;
  callback: (response: GoogleTokenResponse) => void;
  error_callback?: (response: GoogleTokenErrorResponse) => void;
};

type GoogleAccountsOauth2 = {
  initTokenClient: (config: GoogleTokenClientConfig) => GoogleTokenClient;
};

type GoogleAccountsId = {
  initialize: (config: GoogleIdClientConfig) => void;
  prompt: () => void;
  cancel?: () => void;
};

type GoogleNamespace = {
  accounts?: {
    id?: GoogleAccountsId;
    oauth2?: GoogleAccountsOauth2;
  };
};

declare global {
  interface Window {
    google?: GoogleNamespace;
  }
}

export type GoogleTokenType = "idToken" | "accessToken";

export type GoogleOAuthSuccess = {
  token: string;
  tokenType: GoogleTokenType;
};

export class GoogleOAuthError extends Error {
  public readonly code:
    | "oauth_not_configured"
    | "oauth_sdk_load_failed"
    | "oauth_sdk_unavailable"
    | "oauth_popup_closed"
    | "oauth_token_missing"
    | "oauth_request_failed";

  public constructor(code: GoogleOAuthError["code"], message: string) {
    super(message);
    this.code = code;
    this.name = "GoogleOAuthError";
  }
}

let sdkLoadPromise: Promise<void> | null = null;

const getGoogleIdApi = (): GoogleAccountsId | null =>
  window.google?.accounts?.id ?? null;

const getGoogleOauth2Api = (): GoogleAccountsOauth2 | null =>
  window.google?.accounts?.oauth2 ?? null;

const loadGoogleIdentitySdk = async (): Promise<void> => {
  if (getGoogleIdApi() || getGoogleOauth2Api()) {
    return;
  }
  if (sdkLoadPromise) {
    return sdkLoadPromise;
  }

  sdkLoadPromise = new Promise<void>((resolve, reject) => {
    const existing = document.getElementById(
      GOOGLE_IDENTITY_SCRIPT_ID,
    ) as HTMLScriptElement | null;
    if (existing) {
      existing.addEventListener("load", () => resolve(), { once: true });
      existing.addEventListener(
        "error",
        () =>
          reject(
            new GoogleOAuthError(
              "oauth_sdk_load_failed",
              "Не удалось загрузить Google OAuth SDK.",
            ),
          ),
        { once: true },
      );
      return;
    }

    const script = document.createElement("script");
    script.id = GOOGLE_IDENTITY_SCRIPT_ID;
    script.src = GOOGLE_IDENTITY_SCRIPT_SRC;
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () =>
      reject(
        new GoogleOAuthError(
          "oauth_sdk_load_failed",
          "Не удалось загрузить Google OAuth SDK.",
        ),
      );
    document.head.appendChild(script);
  }).finally(() => {
    sdkLoadPromise = null;
  });

  await sdkLoadPromise;
};

const toGoogleAuthError = (message: string): GoogleOAuthError =>
  new GoogleOAuthError("oauth_request_failed", message);

const requestGoogleAccessToken = async (
  api: GoogleAccountsOauth2,
  clientId: string,
): Promise<string> =>
  await new Promise<string>((resolve, reject) => {
    let settled = false;
    const timeoutId = window.setTimeout(() => {
      if (settled) return;
      settled = true;
      reject(
        new GoogleOAuthError(
          "oauth_popup_closed",
          "Вход через Google отменен или не был завершен.",
        ),
      );
    }, GOOGLE_PROMPT_TIMEOUT_MS);

    const finish = (result: { token?: string; error?: GoogleOAuthError }) => {
      if (settled) return;
      settled = true;
      window.clearTimeout(timeoutId);

      if (result.error) {
        reject(result.error);
        return;
      }

      const token = (result.token || "").trim();
      if (!token) {
        reject(
          new GoogleOAuthError(
            "oauth_token_missing",
            "Google OAuth не вернул accessToken.",
          ),
        );
        return;
      }
      resolve(token);
    };

    let tokenClient: GoogleTokenClient;
    try {
      tokenClient = api.initTokenClient({
        client_id: clientId,
        scope: GOOGLE_OAUTH_SCOPE,
        callback: (response) => {
          const errorCode = String(response.error || "").trim();
          if (errorCode) {
            if (errorCode === "popup_closed_by_user") {
              finish({
                error: new GoogleOAuthError(
                  "oauth_popup_closed",
                  "Вход через Google отменен.",
                ),
              });
              return;
            }
            finish({
              error: toGoogleAuthError(
                "Не удалось выполнить вход через Google. Проверьте настройки OAuth и блокировщики контента.",
              ),
            });
            return;
          }

          finish({ token: response.access_token || "" });
        },
        error_callback: (response) => {
          const responseType = String(response.type || "").trim();
          if (responseType === "popup_closed") {
            finish({
              error: new GoogleOAuthError(
                "oauth_popup_closed",
                "Вход через Google отменен.",
              ),
            });
            return;
          }
          finish({
            error: toGoogleAuthError(
              "Не удалось выполнить вход через Google. Проверьте настройки OAuth и блокировщики контента.",
            ),
          });
        },
      });
    } catch {
      finish({
        error: toGoogleAuthError("Не удалось инициализировать Google OAuth."),
      });
      return;
    }

    try {
      tokenClient.requestAccessToken({ prompt: "consent" });
    } catch {
      finish({
        error: new GoogleOAuthError(
          "oauth_popup_closed",
          "Вход через Google отменен.",
        ),
      });
    }
  });

const requestGoogleIdToken = async (
  api: GoogleAccountsId,
  clientId: string,
): Promise<string> =>
  await new Promise<string>((resolve, reject) => {
    let settled = false;
    const timeoutId = window.setTimeout(() => {
      if (settled) return;
      settled = true;
      api.cancel?.();
      reject(
        new GoogleOAuthError(
          "oauth_popup_closed",
          "Вход через Google отменен или не был завершен.",
        ),
      );
    }, GOOGLE_PROMPT_TIMEOUT_MS);

    const finish = (result: { token?: string; error?: GoogleOAuthError }) => {
      if (settled) return;
      settled = true;
      window.clearTimeout(timeoutId);

      if (result.error) {
        reject(result.error);
        return;
      }

      const token = (result.token || "").trim();
      if (!token) {
        reject(
          new GoogleOAuthError(
            "oauth_token_missing",
            "Google OAuth не вернул idToken.",
          ),
        );
        return;
      }
      resolve(token);
    };

    api.initialize({
      client_id: clientId,
      callback: (response) => {
        const credential = (response.credential || "").trim();
        if (!credential) {
          finish({
            error: new GoogleOAuthError(
              "oauth_token_missing",
              "Google OAuth не вернул idToken.",
            ),
          });
          return;
        }
        finish({ token: credential });
      },
      cancel_on_tap_outside: true,
      auto_select: false,
      use_fedcm_for_prompt: false,
      itp_support: true,
    });

    try {
      api.prompt();
    } catch {
      finish({
        error: new GoogleOAuthError(
          "oauth_popup_closed",
          "Вход через Google отменен.",
        ),
      });
    }
  });

export const signInWithGoogle = async (
  clientId: string,
): Promise<GoogleOAuthSuccess> => {
  const normalizedClientId = clientId.trim();
  if (!normalizedClientId) {
    throw new GoogleOAuthError("oauth_not_configured", "Google OAuth не настроен.");
  }

  await loadGoogleIdentitySdk();

  const oauth2Api = getGoogleOauth2Api();
  let oauth2Error: GoogleOAuthError | null = null;
  if (oauth2Api) {
    try {
      const accessToken = await requestGoogleAccessToken(
        oauth2Api,
        normalizedClientId,
      );
      return { token: accessToken, tokenType: "accessToken" };
    } catch (error) {
      oauth2Error =
        error instanceof GoogleOAuthError
          ? error
          : new GoogleOAuthError(
              "oauth_request_failed",
              "Не удалось выполнить вход через Google.",
            );
      if (oauth2Error.code === "oauth_popup_closed") {
        throw oauth2Error;
      }
    }
  }

  const idApi = getGoogleIdApi();
  if (!idApi) {
    if (oauth2Error) {
      throw oauth2Error;
    }
    throw new GoogleOAuthError("oauth_sdk_unavailable", "Google OAuth SDK недоступен.");
  }

  try {
    const idToken = await requestGoogleIdToken(idApi, normalizedClientId);
    return { token: idToken, tokenType: "idToken" };
  } catch (idError) {
    if (oauth2Error) {
      throw oauth2Error;
    }
    throw idError;
  }
};
