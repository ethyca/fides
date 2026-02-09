import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";

import { PrivacyRequestResponse, PrivacyRequestStatus } from "~/types/api";

import { RequestTableActions } from "./RequestTableActions";

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

const mockUseGetConfigurationSettingsQuery = jest.fn();
jest.mock("~/features/config-settings/config-settings.slice", () => ({
  useGetConfigurationSettingsQuery: () =>
    mockUseGetConfigurationSettingsQuery(),
}));

const mockUseGetActiveMessagingProviderQuery = jest.fn();
jest.mock("~/features/messaging/messaging.slice", () => ({
  useGetActiveMessagingProviderQuery: () =>
    mockUseGetActiveMessagingProviderQuery(),
}));

jest.mock("~/features/common/Restrict", () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) => children,
}));

jest.mock("fidesui", () => {
  // eslint-disable-next-line global-require
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

describe("RequestTableActions", () => {
  const baseRequest: PrivacyRequestResponse = {
    id: "pri_123",
    created_at: "2024-01-15T10:00:00Z",
    status: PrivacyRequestStatus.PENDING,
  } as PrivacyRequestResponse;

  beforeEach(() => {
    jest.clearAllMocks();
    mockIsLoading = false;
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

      const approveBtn = screen.getByTestId("privacy-request-approve-btn");
      await user.click(approveBtn);

      const modal = screen.getByTestId("approve-modal");
      expect(modal).toBeInTheDocument();

      const confirmBtn = screen.getByTestId("approve-modal-confirm");
      await user.click(confirmBtn);

      expect(mockHandleApproveRequest).toHaveBeenCalledTimes(1);
      expect(screen.queryByTestId("approve-modal")).not.toBeInTheDocument();
    });

    it("should complete full deny flow from button click to request denial", async () => {
      const user = userEvent.setup();
      render(<RequestTableActions subjectRequest={baseRequest} />);

      const denyBtn = screen.getByTestId("privacy-request-deny-btn");
      await user.click(denyBtn);

      const modal = screen.getByTestId("deny-modal");
      expect(modal).toBeInTheDocument();

      const confirmBtn = screen.getByTestId("deny-modal-confirm");
      await user.click(confirmBtn);

      expect(mockHandleDenyRequest).toHaveBeenCalledWith("Test reason");
      expect(screen.queryByTestId("deny-modal")).not.toBeInTheDocument();
    });

    it("should complete full delete flow from button click to request deletion", async () => {
      const user = userEvent.setup();
      render(<RequestTableActions subjectRequest={baseRequest} />);

      const deleteBtn = screen.getByTestId("privacy-request-delete-btn");
      await user.click(deleteBtn);

      const modal = screen.getByTestId("confirmation-modal");
      expect(modal).toBeInTheDocument();

      const confirmBtn = screen.getByTestId("confirmation-modal-confirm");
      await user.click(confirmBtn);

      expect(mockHandleDeleteRequest).toHaveBeenCalledTimes(1);
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

      const finalizeBtn = screen.getByTestId("privacy-request-finalize-btn");
      await user.click(finalizeBtn);

      const modal = screen.getByTestId("confirmation-modal");
      expect(modal).toBeInTheDocument();

      const confirmBtn = screen.getByTestId("confirmation-modal-confirm");
      await user.click(confirmBtn);

      expect(mockHandleFinalizeRequest).toHaveBeenCalledTimes(1);
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

      await user.tab();
      expect(approveBtn).toHaveFocus();

      await user.keyboard("{Enter}");

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
