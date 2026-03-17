import { createContext } from "react";

import type { WebSocketStatus } from "../../hooks/useReconnectingWebSocket";
import type { OnlineUser } from "../api/users";

export type PresenceContextValue = {
  online: OnlineUser[];
  guests: number;
  status: WebSocketStatus;
  lastError: string | null;
};

export const FALLBACK_PRESENCE: PresenceContextValue = {
  online: [],
  guests: 0,
  status: "idle",
  lastError: null,
};

export const PresenceContext =
  createContext<PresenceContextValue>(FALLBACK_PRESENCE);
