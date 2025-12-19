import { render, screen } from "@testing-library/react";

import { PrivacyRequestResponse, PrivacyRequestStatus } from "~/types/api";

import { RequestTableActions } from "./RequestTableActions";

// Mock the mutations hook
const mockHandleApproveRequest = jest.fn();
const mockHandleDenyRequest = jest.fn();
const mockHandleDeleteRequest = jest.fn();
const mockHandleFinalizeRequest = jest.fn();

jest.mock("./hooks/useMutations", () => ({
  useMutations: () => ({
    handleApproveRequest: mockHandleApproveRequest,
    handleDenyRequest: mockHandleDenyRequest,
    handleDeleteRequest: mockHandleDeleteRequest,
    handleFinalizeRequest: mockHandleFinalizeRequest,
    isLoading: false,
  }),
}));

// Mock the config settings query
jest.mock("~/features/config-settings/config-settings.slice", () => ({
  useGetConfigurationSettingsQuery: () => ({
    data: {
      notifications: {
        send_request_completion_notification: true,
      },
    },
  }),
}));

// Mock the messaging provider query
jest.mock("~/features/messaging/messaging.slice", () => ({
  useGetActiveMessagingProviderQuery: () => ({
    data: {
      service_type: "mailgun",
    },
  }),
}));

// Mock Restrict component to always render children
jest.mock("~/features/common/Restrict", () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) => children,
}));

// Mock fidesui components
jest.mock("fidesui", () => ({
  AntButton: ({ children, onClick, loading, disabled, ...props }: any) => (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-busy={loading ? "true" : undefined}
      {...props}
    >
      {children}
    </button>
  ),
  HStack: ({ children }: any) => <div>{children}</div>,
  Icons: {
    Checkmark: () => <span>Checkmark</span>,
    Close: () => <span>Close</span>,
    Stamp: () => <span>Stamp</span>,
    TrashCan: () => <span>TrashCan</span>,
  },
  Portal: ({ children }: any) => children,
  Text: ({ children }: any) => <span>{children}</span>,
  useDisclosure: () => ({
    isOpen: false,
    onOpen: jest.fn(),
    onClose: jest.fn(),
  }),
}));

// Mock modal components
jest.mock("./ApprovePrivacyRequestModal", () => ({
  __esModule: true,
  default: () => null,
}));

jest.mock("./DenyPrivacyRequestModal", () => ({
  __esModule: true,
  default: () => null,
}));

jest.mock("~/features/common/modals/ConfirmationModal", () => ({
  __esModule: true,
  default: () => null,
}));

describe("RequestTableActions", () => {
  const baseRequest: PrivacyRequestResponse = {
    id: "pri_123",
    created_at: "2024-01-15T10:00:00Z",
    status: PrivacyRequestStatus.PENDING,
  } as PrivacyRequestResponse;

  beforeEach(() => {
    jest.clearAllMocks();
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
      const request = { ...baseRequest, status };

      it(`should ${approve ? "show" : "not show"} approve button`, () => {
        render(<RequestTableActions subjectRequest={request} />);
        const btn = screen.queryByTestId("privacy-request-approve-btn");
        if (approve) {
          expect(btn).toBeInTheDocument();
        } else {
          expect(btn).not.toBeInTheDocument();
        }
      });

      it(`should ${deny ? "show" : "not show"} deny button`, () => {
        render(<RequestTableActions subjectRequest={request} />);
        const btn = screen.queryByTestId("privacy-request-deny-btn");
        if (deny) {
          expect(btn).toBeInTheDocument();
        } else {
          expect(btn).not.toBeInTheDocument();
        }
      });

      it(`should ${finalize ? "show" : "not show"} finalize button`, () => {
        render(<RequestTableActions subjectRequest={request} />);
        const btn = screen.queryByTestId("privacy-request-finalize-btn");
        if (finalize) {
          expect(btn).toBeInTheDocument();
        } else {
          expect(btn).not.toBeInTheDocument();
        }
      });

      it(`should ${deleteBtn ? "show" : "not show"} delete button`, () => {
        render(<RequestTableActions subjectRequest={request} />);
        const btn = screen.queryByTestId("privacy-request-delete-btn");
        if (deleteBtn) {
          expect(btn).toBeInTheDocument();
        } else {
          expect(btn).not.toBeInTheDocument();
        }
      });
    },
  );
});
