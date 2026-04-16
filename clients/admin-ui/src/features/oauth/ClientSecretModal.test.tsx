import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import ClientSecretModal from "./ClientSecretModal";

// ClipboardButton mock: lets us assert what copyText value the button receives
// without needing to invoke the clipboard API or click through Ant Design portals.
jest.mock("~/features/common/ClipboardButton", () => ({
  __esModule: true,
  default: ({ copyText, ...props }: any) => (
    <button
      data-testid="clipboard-btn"
      aria-label="copy"
      type="button"
      data-copy-text={copyText}
      {...props}
    />
  ),
}));

const defaultProps = {
  isOpen: true,
  onClose: jest.fn(),
  clientId: "test-client-id",
  secret: "super-secret-value",
};

describe("ClientSecretModal", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("title", () => {
    it("shows 'Client created' when context is created", () => {
      render(<ClientSecretModal {...defaultProps} context="created" />);
      expect(screen.getByText("Client created")).toBeInTheDocument();
    });

    it("shows 'Secret rotated' when context is rotated", () => {
      render(<ClientSecretModal {...defaultProps} context="rotated" />);
      expect(screen.getByText("Secret rotated")).toBeInTheDocument();
    });
  });

  describe("visibility", () => {
    it("renders nothing when isOpen is false", () => {
      render(
        <ClientSecretModal
          {...defaultProps}
          context="created"
          isOpen={false}
        />,
      );
      expect(screen.queryByTestId("secret-warning")).not.toBeInTheDocument();
    });

    it("renders when isOpen is true", () => {
      render(<ClientSecretModal {...defaultProps} context="created" />);
      expect(screen.getByTestId("secret-warning")).toBeInTheDocument();
    });
  });

  describe("warning", () => {
    it("shows the copy-now warning", () => {
      render(<ClientSecretModal {...defaultProps} context="created" />);
      expect(screen.getByTestId("secret-warning")).toHaveTextContent(
        "Copy this secret now",
      );
    });
  });

  describe("client ID field", () => {
    it("displays the client ID in plain text by default", () => {
      render(<ClientSecretModal {...defaultProps} context="created" />);
      expect(screen.getByDisplayValue("test-client-id")).toBeInTheDocument();
    });

    it("has a copy button for the client ID", () => {
      render(<ClientSecretModal {...defaultProps} context="created" />);
      const copyButtons = screen.getAllByTestId("clipboard-btn");
      const clientIdBtn = copyButtons.find(
        (btn) => btn.getAttribute("data-copy-text") === "test-client-id",
      );
      expect(clientIdBtn).toBeInTheDocument();
    });

    it("does not have a reveal/hide toggle for client ID", () => {
      render(<ClientSecretModal {...defaultProps} context="created" />);
      expect(
        screen.queryByTestId("toggle-reveal-client-id"),
      ).not.toBeInTheDocument();
    });
  });

  describe("secret field", () => {
    it("hides the secret by default", () => {
      render(<ClientSecretModal {...defaultProps} context="created" />);
      expect(
        screen.queryByDisplayValue("super-secret-value"),
      ).not.toBeInTheDocument();
    });

    it("shows bullet placeholders when hidden", () => {
      render(<ClientSecretModal {...defaultProps} context="created" />);
      expect(screen.getByDisplayValue(/^•+$/)).toBeInTheDocument();
    });

    it("reveals the secret when the toggle button is clicked", async () => {
      const user = userEvent.setup();
      render(<ClientSecretModal {...defaultProps} context="created" />);

      await user.click(screen.getByTestId("toggle-reveal-client-secret"));

      expect(screen.getByDisplayValue("super-secret-value")).toBeInTheDocument();
    });

    it("hides the secret again when toggle is clicked a second time", async () => {
      const user = userEvent.setup();
      render(<ClientSecretModal {...defaultProps} context="created" />);

      await user.click(screen.getByTestId("toggle-reveal-client-secret"));
      expect(
        screen.getByDisplayValue("super-secret-value"),
      ).toBeInTheDocument();

      await user.click(screen.getByTestId("toggle-reveal-client-secret"));
      expect(
        screen.queryByDisplayValue("super-secret-value"),
      ).not.toBeInTheDocument();
    });

    it("copy button always receives the real secret value even when field is hidden", () => {
      render(<ClientSecretModal {...defaultProps} context="created" />);

      // Secret field is hidden by default — copy button should still hold the real value
      const copyButtons = screen.getAllByTestId("clipboard-btn");
      const secretCopyBtn = copyButtons.find(
        (btn) => btn.getAttribute("data-copy-text") === "super-secret-value",
      );
      expect(secretCopyBtn).toBeInTheDocument();
    });
  });

  describe("done button", () => {
    it("calls onClose when done button is clicked", async () => {
      const onClose = jest.fn();
      const user = userEvent.setup();
      render(
        <ClientSecretModal
          {...defaultProps}
          context="created"
          onClose={onClose}
        />,
      );

      await user.click(screen.getByTestId("done-btn"));

      expect(onClose).toHaveBeenCalledTimes(1);
    });
  });
});
