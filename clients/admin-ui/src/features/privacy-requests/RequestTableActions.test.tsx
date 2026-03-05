import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";

import { PrivacyRequestResponse, PrivacyRequestStatus } from "~/types/api";

import { RequestTableActions } from "./RequestTableActions";

const mockHandleApproveRequest = jest.fn();
const mockHandleDenyRequest = jest.fn();
const mockHandleDeleteRequest = jest.fn();
const mockHandleFinalizeRequest = jest.fn();
const mockIsLoading = jest.fn();

jest.mock("./hooks/useMutations", () => ({
  useMutations: () => ({
    handleApproveRequest: mockHandleApproveRequest,
    handleDenyRequest: mockHandleDenyRequest,
    handleDeleteRequest: mockHandleDeleteRequest,
    handleFinalizeRequest: mockHandleFinalizeRequest,
    get isLoading() {
      return mockIsLoading();
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
    Button: ({ children, onClick, loading, disabled, icon, ...props }: any) => (
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
    ChakraHStack: ({ children, ...props }: any) => (
      <div {...props}>{children}</div>
    ),
    ChakraPortal: ({ children }: any) => <div>{children}</div>,
    ChakraText: ({ children }: any) => <span>{children}</span>,
    ChakraStackProps: {},
    Icons: {
      Checkmark: () => <span>✓</span>,
      Close: () => <span>✕</span>,
      Stamp: () => <span>🔖</span>,
      TrashCan: ({ size }: any) => <span data-size={size}>🗑</span>,
    },
    useChakraDisclosure: () => {
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
    mockIsLoading.mockReturnValue(false);
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
      mockIsLoading.mockReturnValue(true);
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
