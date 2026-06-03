import { lazy } from "react";

export const ChatTargetPage = lazy(() =>
  import("../pages/ChatTargetPage").then((module) => ({
    default: module.ChatTargetPage,
  })),
);

export const FriendsPage = lazy(() =>
  import("../pages/FriendsPage").then((module) => ({
    default: module.FriendsPage,
  })),
);

export const GroupsPage = lazy(() =>
  import("../pages/GroupsPage").then((module) => ({
    default: module.GroupsPage,
  })),
);

export const HomePage = lazy(() =>
  import("../pages/HomePage").then((module) => ({
    default: module.HomePage,
  })),
);

export const InvitePreviewPage = lazy(() =>
  import("../pages/InvitePreviewPage").then((module) => ({
    default: module.InvitePreviewPage,
  })),
);

export const LoginPage = lazy(() =>
  import("../pages/LoginPage").then((module) => ({
    default: module.LoginPage,
  })),
);

export const NotFoundPage = lazy(() =>
  import("../pages/NotFoundPage").then((module) => ({
    default: module.NotFoundPage,
  })),
);

export const RegisterPage = lazy(() =>
  import("../pages/RegisterPage").then((module) => ({
    default: module.RegisterPage,
  })),
);

export const SettingsPage = lazy(() =>
  import("../pages/SettingsPage").then((module) => ({
    default: module.SettingsPage,
  })),
);

export const UserProfilePage = lazy(() =>
  import("../pages/UserProfilePage").then((module) => ({
    default: module.UserProfilePage,
  })),
);
