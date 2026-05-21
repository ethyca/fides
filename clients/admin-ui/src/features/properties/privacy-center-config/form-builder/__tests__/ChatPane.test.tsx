import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ChatPane } from "../ChatPane";

// Bubble.List uses IntersectionObserver for autoScroll; jsdom doesn't provide it.
beforeAll(() => {
  global.IntersectionObserver = class IntersectionObserver {
    // eslint-disable-next-line class-methods-use-this
    observe() {}

    // eslint-disable-next-line class-methods-use-this
    unobserve() {}

    // eslint-disable-next-line class-methods-use-this
    disconnect() {}
  } as unknown as typeof globalThis.IntersectionObserver;
});

describe("ChatPane", () => {
  it("shows empty state when no messages", () => {
    render(
      <ChatPane
        messages={[]}
        status="idle"
        error={null}
        onSend={jest.fn()}
        onAbort={jest.fn()}
      />,
    );
    expect(screen.getByText(/describe the form you want/i)).toBeInTheDocument();
  });

  it("renders messages via Bubble components", () => {
    render(
      <ChatPane
        messages={[
          { role: "user", content: "Add an email field" },
          { role: "assistant", content: "Updated the form (1 field)." },
        ]}
        status="idle"
        error={null}
        onSend={jest.fn()}
        onAbort={jest.fn()}
      />,
    );
    expect(screen.getByText("Add an email field")).toBeInTheDocument();
    expect(screen.getByText("Updated the form (1 field).")).toBeInTheDocument();
  });

  it("renders an error banner when error is set", () => {
    render(
      <ChatPane
        messages={[]}
        status="error"
        error="provider timeout"
        onSend={jest.fn()}
        onAbort={jest.fn()}
      />,
    );
    expect(screen.getByText(/provider timeout/i)).toBeInTheDocument();
  });

  it("disables input when disabled prop is set", () => {
    render(
      <ChatPane
        messages={[]}
        status="idle"
        error={null}
        disabled
        disabledReason="LLM provider not configured."
        onSend={jest.fn()}
        onAbort={jest.fn()}
      />,
    );
    expect(screen.getByText(/LLM provider not configured/)).toBeInTheDocument();
  });

  it("calls onSend with the typed text", async () => {
    const onSend = jest.fn();
    render(
      <ChatPane
        messages={[]}
        status="idle"
        error={null}
        onSend={onSend}
        onAbort={jest.fn()}
      />,
    );

    const textbox = screen.getByRole("textbox");
    await userEvent.type(textbox, "Add an email field");
    // Sender submits on Enter
    await userEvent.keyboard("{Enter}");

    expect(onSend).toHaveBeenCalledWith("Add an email field");
  });
});
