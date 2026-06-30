import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

vi.mock("../pages/HomePage", () => ({
  HomePage: () => <div>HOME_PAGE</div>,
}));

vi.mock("../pages/LoginPage", () => ({
  LoginPage: () => <div>LOGIN_PAGE</div>,
}));

vi.mock("../pages/RegisterPage", () => ({
  RegisterPage: () => <div>REGISTER_PAGE</div>,
}));

vi.mock("../pages/SettingsPage", () => ({
  SettingsPage: () => <div>SETTINGS_PAGE</div>,
}));

vi.mock("../pages/FriendsPage", () => ({
  FriendsPage: () => <div>FRIENDS_PAGE</div>,
}));

vi.mock("../pages/GroupsPage", () => ({
  GroupsPage: () => <div>GROUPS_PAGE</div>,
}));

vi.mock("../pages/InvitePreviewPage", () => ({
  InvitePreviewPage: ({ code }: { code: string }) => (
    <div>INVITE_PAGE:{code}</div>
  ),
}));

vi.mock("../pages/UserProfilePage", () => ({
  UserProfilePage: ({ username }: { username: string }) => (
    <div>USER_PAGE:{username}</div>
  ),
}));

vi.mock("../pages/ChatTargetPage", () => ({
  ChatTargetPage: ({ target }: { target: string }) => (
    <div>CHAT_TARGET_PAGE:{target}</div>
  ),
}));

vi.mock("../pages/NotFoundPage", () => ({
  NotFoundPage: () => <div>NOT_FOUND_PAGE</div>,
}));

import { AppRoutes } from "./routes";

const handlers = {
  onNavigate: vi.fn(),
  onLogin: vi.fn(async () => {}),
  onGoogleOAuth: vi.fn(async () => {}),
  onRegister: vi.fn(async () => {}),
  onLogout: vi.fn(async () => {}),
  onProfileSave: vi.fn(async () => ({ ok: true as const })),
};

describe("AppRoutes", () => {
  it("renders login route", async () => {
    render(
      <MemoryRouter initialEntries={["/login"]}>
        <AppRoutes
          user={null}
          passwordRules={[]}
          googleAuthDisabledReason={null}
          {...handlers}
        />
      </MemoryRouter>,
    );
    expect(await screen.findByText("LOGIN_PAGE")).toBeInTheDocument();
  });

  it("renders register route", async () => {
    render(
      <MemoryRouter initialEntries={["/register"]}>
        <AppRoutes
          user={null}
          passwordRules={[]}
          googleAuthDisabledReason={null}
          {...handlers}
        />
      </MemoryRouter>,
    );
    expect(await screen.findByText("REGISTER_PAGE")).toBeInTheDocument();
  });

  it("renders prefixless direct target route", async () => {
    render(
      <MemoryRouter initialEntries={["/@alice"]}>
        <AppRoutes
          user={null}
          passwordRules={[]}
          googleAuthDisabledReason={null}
          {...handlers}
        />
      </MemoryRouter>,
    );
    expect(
      await screen.findByText("CHAT_TARGET_PAGE:@alice"),
    ).toBeInTheDocument();
  });

  it("renders public chat route through chat target page", async () => {
    render(
      <MemoryRouter initialEntries={["/public"]}>
        <AppRoutes
          user={null}
          passwordRules={[]}
          googleAuthDisabledReason={null}
          {...handlers}
        />
      </MemoryRouter>,
    );
    expect(
      await screen.findByText("CHAT_TARGET_PAGE:public"),
    ).toBeInTheDocument();
  });

  it("keeps reserved routes above catch-all target route", async () => {
    render(
      <MemoryRouter initialEntries={["/friends"]}>
        <AppRoutes
          user={null}
          passwordRules={[]}
          googleAuthDisabledReason={null}
          {...handlers}
        />
      </MemoryRouter>,
    );
    expect(await screen.findByText("FRIENDS_PAGE")).toBeInTheDocument();
  });

  it("renders the dedicated settings route", async () => {
    render(
      <MemoryRouter initialEntries={["/settings"]}>
        <AppRoutes
          user={null}
          passwordRules={[]}
          googleAuthDisabledReason={null}
          {...handlers}
        />
      </MemoryRouter>,
    );
    expect(await screen.findByText("SETTINGS_PAGE")).toBeInTheDocument();
  });

  it("normalizes user profile route by trimming one leading @", async () => {
    render(
      <MemoryRouter initialEntries={["/users/%40%40%40%40"]}>
        <AppRoutes
          user={null}
          passwordRules={[]}
          googleAuthDisabledReason={null}
          {...handlers}
        />
      </MemoryRouter>,
    );
    expect(await screen.findByText("USER_PAGE:@@@")).toBeInTheDocument();
  });

  it("keeps reserved /direct route out of chat resolution", async () => {
    render(
      <MemoryRouter initialEntries={["/direct"]}>
        <AppRoutes
          user={null}
          passwordRules={[]}
          googleAuthDisabledReason={null}
          {...handlers}
        />
      </MemoryRouter>,
    );
    expect(await screen.findByText("NOT_FOUND_PAGE")).toBeInTheDocument();
  });

  it("renders not found for deep unmatched paths", async () => {
    render(
      <MemoryRouter initialEntries={["/some/deep/path"]}>
        <AppRoutes
          user={null}
          passwordRules={[]}
          googleAuthDisabledReason={null}
          {...handlers}
        />
      </MemoryRouter>,
    );
    expect(await screen.findByText("NOT_FOUND_PAGE")).toBeInTheDocument();
  });
});
