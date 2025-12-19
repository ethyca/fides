import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";

import { PrivacyRequestResponse, PrivacyRequestStatus } from "~/types/api";

import { RequestTableActions } from "./RequestTableActions";

// Mock the mutations hook
const mockHandleApproveRequest = jest.fn();
const mockHandleDenyRequest = jest.fn();
const mockHandleDeleteRequest = jest.fn();
const mockHandleFinalizeRequest = jest.fn();
let mockIsLoading = false;

jest.mock("./hooks/useMutations", () => ({
  useMutations: () => ({
    handleApproveRequest: mockHandleApproveRequest,
    handleDenyRequest: mockHandleDenyRequest,
    handleDeleteRequest: mockHandleDeleteRequest,
    handleFinalizeRequest: mockHandleFinalizeRequest,
    get isLoading() {
      return mockIsLoading;
    },
  }),
}));

// Mock the config settings query
const mockUseGetConfigurationSettingsQuery = jest.fn();
jest.mock("~/features/config-settings/config-settings.slice", () => ({
  useGetConfigurationSettingsQuery: () =>
    mockUseGetConfigurationSettingsQuery(),
}));

// Mock the messaging provider query
const mockUseGetActiveMessagingProviderQuery = jest.fn();
jest.mock("~/features/messaging/messaging.slice", () => ({
  useGetActiveMessagingProviderQuery: () =>
    mockUseGetActiveMessagingProviderQuery(),
}));

// Mock Restrict component to always render children
jest.mock("~/features/common/Restrict", () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) => children,
}));

// Mock fidesui components for testing
jest.mock("fidesui", () => {
  // We need to import React inside the factory
  const react = require("react");

  return {
    AntButton: ({
      children,
      onClick,
      loading,
      disabled,
      icon,
      ...props
    }: any) => (
      <button
        type="button"
        onClick={onClick}
        disabled={disabled}
        aria-busy={loading ? "true" : undefined}
        {...props}
      >
        {icon}
        {children}
      </button>
    ),
    HStack: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    Icons: {
      Checkmark: () => <span>✓</span>,
      Close: () => <span>✕</span>,
      Stamp: () => <span>🔖</span>,
      TrashCan: ({ size }: any) => <span data-size={size}>🗑</span>,
    },
    Portal: ({ children }: any) => <div>{children}</div>,
    Text: ({ children }: any) => <span>{children}</span>,
    useDisclosure: () => {
      const [isOpen, setIsOpen] = react.useState(false);

      return {
        isOpen,
        onOpen: () => setIsOpen(true),
        onClose: () => setIsOpen(false),
      };
    },
  };
});

// Note: fidesui is mocked globally in jest.setup.ts

// Mock modal components but make them testable
jest.mock("./ApprovePrivacyRequestModal", () => ({
  __esModule: true,
  default: ({ isOpen, onApproveRequest, onClose }: any) =>
    isOpen ? (
      <div data-testid="approve-modal">
        <button
          data-testid="approve-modal-confirm"
          onClick={() => {
            onApproveRequest();
            onClose();
          }}
          type="button"
        >
          Confirm Approve
        </button>
      </div>
    ) : null,
}));

jest.mock("./DenyPrivacyRequestModal", () => ({
  __esModule: true,
  default: ({ isOpen, onDenyRequest, onClose }: any) =>
    isOpen ? (
      <div data-testid="deny-modal">
        <button
          data-testid="deny-modal-confirm"
          onClick={() => {
            onDenyRequest("Test reason");
            onClose();
          }}
          type="button"
        >
          Confirm Deny
        </button>
      </div>
    ) : null,
}));

jest.mock("~/features/common/modals/ConfirmationModal", () => ({
  __esModule: true,
  default: ({ isOpen, onConfirm, onClose }: any) =>
    isOpen ? (
      <div data-testid="confirmation-modal">
        <button
          data-testid="confirmation-modal-confirm"
          onClick={() => {
            onConfirm();
            onClose();
          }}
          type="button"
        >
          Confirm
        </button>
      </div>
    ) : null,
}));

// Helper to check button visibility
const expectButtonVisibility = (
  button: HTMLElement | null,
  shouldBeVisible: boolean,
) => {
  if (shouldBeVisible) {
    expect(button).toBeInTheDocument();
  } else {
    expect(button).not.toBeInTheDocument();
  }
};

describe("RequestTableActions", () => {
  const baseRequest: PrivacyRequestResponse = {
    id: "pri_123",
    created_at: "2024-01-15T10:00:00Z",
    status: PrivacyRequestStatus.PENDING,
  } as PrivacyRequestResponse;

  beforeEach(() => {
    jest.clearAllMocks();
    mockIsLoading = false; // Reset loading state before each test
    mockUseGetConfigurationSettingsQuery.mockReturnValue({
      data: {
        notifications: {
          send_request_completion_notification: true,
        },
      },
    });
    mockUseGetActiveMessagingProviderQuery.mockReturnValue({
      data: {
        service_type: "mailgun",
      },
    });
  });

  /**
   * Action visibility matrix for all privacy request statuses.
   * This table drives the parameterized tests below.
   */
  const actionVisibilityByStatus = [
    {
      status: PrivacyRequestStatus.PENDING,
      approve: true,
      deny: true,
      finalize: false,
      delete: true,
    },
    {
      status: PrivacyRequestStatus.DUPLICATE,
      approve: true,
      deny: true,
      finalize: false,
      delete: true,
    },
    {
      status: PrivacyRequestStatus.IDENTITY_UNVERIFIED,
      approve: false,
      deny: false,
      finalize: false,
      delete: true,
    },
    {
      status: PrivacyRequestStatus.REQUIRES_INPUT,
      approve: false,
      deny: false,
      finalize: false,
      delete: true,
    },
    {
      status: PrivacyRequestStatus.APPROVED,
      approve: false,
      deny: false,
      finalize: false,
      delete: true,
    },
    {
      status: PrivacyRequestStatus.DENIED,
      approve: false,
      deny: false,
      finalize: false,
      delete: true,
    },
    {
      status: PrivacyRequestStatus.IN_PROCESSING,
      approve: false,
      deny: false,
      finalize: false,
      delete: true,
    },
    {
      status: PrivacyRequestStatus.COMPLETE,
      approve: false,
      deny: false,
      finalize: false,
      delete: true,
    },
    {
      status: PrivacyRequestStatus.PAUSED,
      approve: false,
      deny: false,
      finalize: false,
      delete: true,
    },
    {
      status: PrivacyRequestStatus.ERROR,
      approve: false,
      deny: false,
      finalize: false,
      delete: true,
    },
    {
      status: PrivacyRequestStatus.CANCELED,
      approve: false,
      deny: false,
      finalize: false,
      delete: true,
    },
    {
      status: PrivacyRequestStatus.AWAITING_EMAIL_SEND,
      approve: false,
      deny: false,
      finalize: false,
      delete: true,
    },
    {
      status: PrivacyRequestStatus.REQUIRES_MANUAL_FINALIZATION,
      approve: false,
      deny: false,
      finalize: true,
      delete: true,
    },
  ];

  describe.each(actionVisibilityByStatus)(
    "Action visibility for $status",
    ({ status, approve, deny, finalize, delete: deleteBtn }) => {
      it("should show/hide all action buttons correctly", () => {
        const request = { ...baseRequest, status };
        render(<RequestTableActions subjectRequest={request} />);

        const buttons = {
          approve: screen.queryByTestId("privacy-request-approve-btn"),
          deny: screen.queryByTestId("privacy-request-deny-btn"),
          finalize: screen.queryByTestId("privacy-request-finalize-btn"),
          delete: screen.queryByTestId("privacy-request-delete-btn"),
        };

        expectButtonVisibility(buttons.approve, approve);
        expectButtonVisibility(buttons.deny, deny);
        expectButtonVisibility(buttons.finalize, finalize);
        expectButtonVisibility(buttons.delete, deleteBtn);
      });
    },
  );

  describe("Button interactions", () => {
    it("should open approve modal when approve button is clicked", async () => {
      const user = userEvent.setup();
      render(<RequestTableActions subjectRequest={baseRequest} />);

      const approveBtn = screen.getByTestId("privacy-request-approve-btn");
      await user.click(approveBtn);

      const modal = screen.getByTestId("approve-modal");
      expect(modal).toBeInTheDocument();
    });

    it("should open deny modal when deny button is clicked", async () => {
      const user = userEvent.setup();
      render(<RequestTableActions subjectRequest={baseRequest} />);

      const denyBtn = screen.getByTestId("privacy-request-deny-btn");
      await user.click(denyBtn);

      const modal = screen.getByTestId("deny-modal");
      expect(modal).toBeInTheDocument();
    });

    it("should open delete modal when delete button is clicked", async () => {
      const user = userEvent.setup();
      render(<RequestTableActions subjectRequest={baseRequest} />);

      const deleteBtn = screen.getByTestId("privacy-request-delete-btn");
      await user.click(deleteBtn);

      const modal = screen.getByTestId("confirmation-modal");
      expect(modal).toBeInTheDocument();
    });

    it("should open finalize modal when finalize button is clicked", async () => {
      const user = userEvent.setup();
      const request = {
        ...baseRequest,
        status: PrivacyRequestStatus.REQUIRES_MANUAL_FINALIZATION,
      };
      render(<RequestTableActions subjectRequest={request} />);

      const finalizeBtn = screen.getByTestId("privacy-request-finalize-btn");
      await user.click(finalizeBtn);

      const modal = screen.getByTestId("confirmation-modal");
      expect(modal).toBeInTheDocument();
    });
  });

  describe("Loading states", () => {
    beforeEach(() => {
      mockIsLoading = true;
    });

    it("should disable buttons when loading", () => {
      render(<RequestTableActions subjectRequest={baseRequest} />);

      const approveBtn = screen.getByTestId("privacy-request-approve-btn");
      const denyBtn = screen.getByTestId("privacy-request-deny-btn");
      const deleteBtn = screen.getByTestId("privacy-request-delete-btn");

      expect(approveBtn).toBeDisabled();
      expect(denyBtn).toBeDisabled();
      expect(deleteBtn).toBeDisabled();
    });

    it("should show loading state on buttons", () => {
      render(<RequestTableActions subjectRequest={baseRequest} />);

      const approveBtn = screen.getByTestId("privacy-request-approve-btn");
      expect(approveBtn).toHaveAttribute("aria-busy", "true");
    });
  });

  describe("Complete user flows", () => {
    it("should complete full approval flow from button click to request approval", async () => {
      const user = userEvent.setup();
      render(<RequestTableActions subjectRequest={baseRequest} />);

      // Click approve button
      const approveBtn = screen.getByTestId("privacy-request-approve-btn");
      await user.click(approveBtn);

      // Verify modal opens
      const modal = screen.getByTestId("approve-modal");
      expect(modal).toBeInTheDocument();

      // Confirm approval in modal
      const confirmBtn = screen.getByTestId("approve-modal-confirm");
      await user.click(confirmBtn);

      // Verify the mutation was called
      expect(mockHandleApproveRequest).toHaveBeenCalledTimes(1);

      // Verify modal closes
      expect(screen.queryByTestId("approve-modal")).not.toBeInTheDocument();
    });

    it("should complete full deny flow from button click to request denial", async () => {
      const user = userEvent.setup();
      render(<RequestTableActions subjectRequest={baseRequest} />);

      // Click deny button
      const denyBtn = screen.getByTestId("privacy-request-deny-btn");
      await user.click(denyBtn);

      // Verify modal opens
      const modal = screen.getByTestId("deny-modal");
      expect(modal).toBeInTheDocument();

      // Confirm denial in modal
      const confirmBtn = screen.getByTestId("deny-modal-confirm");
      await user.click(confirmBtn);

      // Verify the mutation was called with reason
      expect(mockHandleDenyRequest).toHaveBeenCalledWith("Test reason");

      // Verify modal closes
      expect(screen.queryByTestId("deny-modal")).not.toBeInTheDocument();
    });

    it("should complete full delete flow from button click to request deletion", async () => {
      const user = userEvent.setup();
      render(<RequestTableActions subjectRequest={baseRequest} />);

      // Click delete button
      const deleteBtn = screen.getByTestId("privacy-request-delete-btn");
      await user.click(deleteBtn);

      // Verify modal opens
      const modal = screen.getByTestId("confirmation-modal");
      expect(modal).toBeInTheDocument();

      // Confirm deletion in modal
      const confirmBtn = screen.getByTestId("confirmation-modal-confirm");
      await user.click(confirmBtn);

      // Verify the mutation was called
      expect(mockHandleDeleteRequest).toHaveBeenCalledTimes(1);

      // Verify modal closes
      expect(
        screen.queryByTestId("confirmation-modal"),
      ).not.toBeInTheDocument();
    });

    it("should complete full finalize flow from button click to request finalization", async () => {
      const user = userEvent.setup();
      const request = {
        ...baseRequest,
        status: PrivacyRequestStatus.REQUIRES_MANUAL_FINALIZATION,
      };
      render(<RequestTableActions subjectRequest={request} />);

      // Click finalize button
      const finalizeBtn = screen.getByTestId("privacy-request-finalize-btn");
      await user.click(finalizeBtn);

      // Verify modal opens
      const modal = screen.getByTestId("confirmation-modal");
      expect(modal).toBeInTheDocument();

      // Confirm finalization in modal
      const confirmBtn = screen.getByTestId("confirmation-modal-confirm");
      await user.click(confirmBtn);

      // Verify the mutation was called
      expect(mockHandleFinalizeRequest).toHaveBeenCalledTimes(1);

      // Verify modal closes
      expect(
        screen.queryByTestId("confirmation-modal"),
      ).not.toBeInTheDocument();
    });
  });

  describe("Keyboard navigation", () => {
    it("should open modal via keyboard interaction with approve button", async () => {
      const user = userEvent.setup();
      render(<RequestTableActions subjectRequest={baseRequest} />);

      const approveBtn = screen.getByTestId("privacy-request-approve-btn");

      // Navigate to button and activate with Enter
      await user.tab();
      expect(approveBtn).toHaveFocus();

      await user.keyboard("{Enter}");

      // Verify modal opens
      const modal = screen.getByTestId("approve-modal");
      expect(modal).toBeInTheDocument();
    });

    it("should allow tab navigation between action buttons", async () => {
      const user = userEvent.setup();
      render(<RequestTableActions subjectRequest={baseRequest} />);

      const approveBtn = screen.getByTestId("privacy-request-approve-btn");
      const denyBtn = screen.getByTestId("privacy-request-deny-btn");

      await user.tab();
      expect(approveBtn).toHaveFocus();

      await user.tab();
      expect(denyBtn).toHaveFocus();
    });
  });
});
