import { z } from "zod";

import { normalizePublicRef } from "../../shared/lib/publicRef";

/**
 * Декодирует roomRef из route-параметра.
 * Разрешены: `public` и положительный roomId.
 */
export const decodeRoomRefParam = (value: unknown): string | null => {
  if (value === "public") return "public";
  const parsed = z.string().regex(/^\d+$/).safeParse(value);
  if (!parsed.success) return null;
  const numeric = Number(parsed.data);
  if (!Number.isFinite(numeric) || numeric <= 0) return null;
  return String(Math.trunc(numeric));
};

/**
 * Декодирует public ref из route-параметра.
 * Нормализует `@handle` -> `handle`.
 */
export const decodePublicRefParam = (value: unknown): string | null => {
  const parsed = z.string().safeParse(value);
  if (!parsed.success) return null;
  const normalized = normalizePublicRef(parsed.data);
  return normalized.length > 0 ? normalized : null;
};
