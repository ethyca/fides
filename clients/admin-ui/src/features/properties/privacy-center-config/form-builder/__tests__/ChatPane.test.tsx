import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ChatPane } from "../ChatPane";

describe("ChatPane", () => {
  it("disables submit when streaming and shows abort button", () => {
    render(
      <ChatPane
        messages={[]}
        status="streaming"
        error={null}
        onSend={jest.fn()}
        onAbort={jest.fn()}
      />,
    );
    expect(screen.getByRole("button", { name: /stop/i })).toBeEnabled();
    expect(screen.getByRole("textbox")).toBeDisabled();
  });

  it("calls onSend with the typed text and clears input", async () => {
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
    await userEvent.click(screen.getByRole("button", { name: /send/i }));

    expect(onSend).toHaveBeenCalledWith("Add an email field");
    expect(textbox).toHaveValue("");
  });

  it("renders an error banner when status='error'", () => {
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
});
