import { beforeEach, describe, expect, it } from "vitest";

import {
  DIRECT_HOME_FALLBACK_PATH,
  parseDirectRefFromPathname,
  rememberLastDirectRef,
  resolveRememberedDirectPath,
} from "./directNavigation";

describe("directNavigation", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("parses direct ref from pathname", () => {
    expect(parseDirectRefFromPathname("/direct/alice")).toBe("alice");
    expect(parseDirectRefFromPathname("/rooms/public")).toBeNull();
  });

  it("prefers active direct pathname", () => {
    rememberLastDirectRef("bob");

    expect(
      resolveRememberedDirectPath({
        pathname: "/direct/alice",
        directPeerRefs: ["charlie"],
      }),
    ).toBe("/direct/alice");
  });

  it("falls back to stored direct ref and then to friends", () => {
    expect(resolveRememberedDirectPath()).toBe(DIRECT_HOME_FALLBACK_PATH);

    rememberLastDirectRef("bob");
    expect(resolveRememberedDirectPath()).toBe("/direct/bob");
  });

  it("uses first known inbox peer when storage is empty", () => {
    expect(
      resolveRememberedDirectPath({
        directPeerRefs: ["", null, "alice"],
      }),
    ).toBe("/direct/alice");
  });
});
