import type { AxiosInstance } from "axios";
import { describe, expect, it, vi } from "vitest";

import { updateProfile } from "./updateProfile";

const profileResponse = {
  data: {
    user: {
      name: "Updated User",
      handle: "updated",
      publicId: "1234567890",
      publicRef: "@updated",
      profileImage: null,
      avatarCrop: null,
      bio: "about me",
      lastSeen: null,
      registeredAt: null,
    },
  },
};

describe("updateProfile", () => {
  it("uses the multipart transport for profile fields", async () => {
    const patchForm = vi.fn().mockResolvedValue(profileResponse);
    const patch = vi.fn();
    const apiClient = {
      patch,
      patchForm,
    } as unknown as AxiosInstance;

    await updateProfile(apiClient, {
      bio: "about me",
    });

    expect(patchForm).toHaveBeenCalledOnce();
    const [endpoint, body] = patchForm.mock.calls[0] as [string, FormData];
    expect(endpoint).toBe("/profile/");
    expect(body).toBeInstanceOf(FormData);
    expect(Object.fromEntries(body.entries())).toEqual({
      bio: "about me",
    });
    expect(patch).not.toHaveBeenCalled();
  });
});
