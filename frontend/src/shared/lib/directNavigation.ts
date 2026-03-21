import { buildDirectPath, normalizePublicRef } from "./publicRef";

export const LAST_DIRECT_REF_STORAGE_KEY = "ui.direct.last-ref";
export const DIRECT_HOME_FALLBACK_PATH = "/friends";

export const parseDirectRefFromPathname = (pathname: string): string | null => {
  if (!pathname.startsWith("/direct/")) return null;
  const ref = pathname.slice("/direct/".length).split("/")[0] || "";
  if (!ref) return null;
  try {
    return normalizePublicRef(decodeURIComponent(ref));
  } catch {
    return normalizePublicRef(ref);
  }
};

export const readStoredLastDirectRef = (): string => {
  if (typeof window === "undefined") return "";
  return normalizePublicRef(
    window.localStorage.getItem(LAST_DIRECT_REF_STORAGE_KEY),
  );
};

export const rememberLastDirectRef = (value: string | null | undefined): void => {
  if (typeof window === "undefined") return;
  const normalized = normalizePublicRef(value);
  if (!normalized) return;
  window.localStorage.setItem(LAST_DIRECT_REF_STORAGE_KEY, normalized);
};

type ResolveRememberedDirectPathOptions = {
  pathname?: string;
  fallbackPath?: string;
  directPeerRefs?: Array<string | null | undefined>;
};

export const resolveRememberedDirectPath = ({
  pathname,
  fallbackPath = DIRECT_HOME_FALLBACK_PATH,
  directPeerRefs = [],
}: ResolveRememberedDirectPathOptions = {}): string => {
  const activeDirectRef = pathname ? parseDirectRefFromPathname(pathname) : null;
  if (activeDirectRef) return buildDirectPath(activeDirectRef);

  const storedDirectRef = readStoredLastDirectRef();
  if (storedDirectRef) return buildDirectPath(storedDirectRef);

  for (const peerRef of directPeerRefs) {
    const normalized = normalizePublicRef(peerRef);
    if (normalized) return buildDirectPath(normalized);
  }

  return fallbackPath;
};
