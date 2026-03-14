/**
 * Выполняет функцию `getWebSocketBase`.
 * @returns Результат выполнения `getWebSocketBase`.
 */

export const getWebSocketBase = () => {
  const scheme = window.location.protocol === "https:" ? "wss" : "ws";
  if (import.meta.env.DEV) {
    // In dev, route WS through Vite proxy (/ws -> backend) to keep
    // same-origin browser behavior and avoid cross-origin handshake issues.
    return `${scheme}://${window.location.host}`;
  }
  return `${scheme}://${window.location.host}`;
};
