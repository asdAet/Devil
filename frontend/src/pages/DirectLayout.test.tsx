import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("./DirectChatByUsernamePage", () => ({
  DirectChatByUsernamePage: ({ publicRef }: { publicRef: string }) => (
    <div>CHAT:{publicRef}</div>
  ),
}));

import { DirectLayout } from "./DirectLayout";

const user = {
  username: "demo",
  email: "demo@example.com",
  profileImage: null,
  bio: "",
  lastSeen: null,
  registeredAt: null,
};

describe("DirectLayout", () => {
  it("shows placeholder when no active chat", () => {
    render(<DirectLayout user={user} onNavigate={vi.fn()} />);
    expect(
      screen.getByText(
        "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0434\u0438\u0430\u043b\u043e\u0433 \u0432 \u0431\u043e\u043a\u043e\u0432\u043e\u0439 \u043f\u0430\u043d\u0435\u043b\u0438, \u0447\u0442\u043e\u0431\u044b \u043d\u0430\u0447\u0430\u0442\u044c \u0447\u0430\u0442.",
      ),
    ).toBeInTheDocument();
  });

  it("shows chat when ref is provided", () => {
    render(<DirectLayout user={user} publicRef="alice" onNavigate={vi.fn()} />);
    expect(screen.getByText("CHAT:alice")).toBeInTheDocument();
  });
});
