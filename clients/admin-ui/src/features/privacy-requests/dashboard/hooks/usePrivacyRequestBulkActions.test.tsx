import { act, renderHook } from "@testing-library/react";
import { MenuProps } from "fidesui";

import { PrivacyRequestResponse, PrivacyRequestStatus } from "~/types/api";

import { BulkActionType } from "../../helpers";
import { usePrivacyRequestBulkActions } from "./usePrivacyRequestBulkActions";

const mockBulkApproveRequest = jest.fn();
const mockBulkDenyRequest = jest.fn();
const mockBulkSoftDeleteRequest = jest.fn();
const mockBulkFinalizeRequest = jest.fn();
const mockOpenDenyPrivacyRequestModal = jest.fn();

jest.mock("../../privacy-requests.slice", () => ({
  useBulkApproveRequestMutation: () => [mockBulkApproveRequest],
  useBulkDenyRequestMutation: () => [mockBulkDenyRequest],
  useBulkSoftDeleteRequestMutation: () => [mockBulkSoftDeleteRequest],
  useBulkFinalizeRequestMutation: () => [mockBulkFinalizeRequest],
}));

jest.mock("../../hooks/useDenyRequestModal", () => ({
  useDenyPrivacyRequestModal: () => ({
    openDenyPrivacyRequestModal: mockOpenDenyPrivacyRequestModal,
  }),
}));

const mockMessageApi = {
  loading: jest.fn(() => jest.fn()),
  success: jest.fn(),
  error: jest.fn(),
  warning: jest.fn(),
};

const mockModalApi = {
  confirm: jest.fn(),
  info: jest.fn(),
  success: jest.fn(),
  error: jest.fn(),
  warning: jest.fn(),
} as any;

jest.mock("fidesui", () => ({
  useMessage: jest.fn(() => mockMessageApi),
  useModal: jest.fn(() => mockModalApi),
  Icons: {
    Checkmark: () => null,
    Close: () => null,
    TrashCan: () => null,
    Stamp: () => null,
  },
}));

describe("usePrivacyRequestBulkActions", () => {
  // Shared test data
  const pendingRequest1: PrivacyRequestResponse = {
    id: "1",
    status: PrivacyRequestStatus.PENDING,
  } as PrivacyRequestResponse;

  const pendingRequest2: PrivacyRequestResponse = {
    id: "2",
    status: PrivacyRequestStatus.PENDING,
  } as PrivacyRequestResponse;

  const completeRequest: PrivacyRequestResponse = {
    id: "3",
    status: PrivacyRequestStatus.COMPLETE,
  } as PrivacyRequestResponse;

  const requiresFinalizationRequest: PrivacyRequestResponse = {
    id: "4",
    status: PrivacyRequestStatus.REQUIRES_MANUAL_FINALIZATION,
  } as PrivacyRequestResponse;

  const mockRequests: PrivacyRequestResponse[] = [
    pendingRequest1,
    completeRequest,
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    mockMessageApi.loading.mockReturnValue(jest.fn());
  });

  it("returns correct menu items with proper disabled states", () => {
    const { result } = renderHook(() =>
      usePrivacyRequestBulkActions({
        requests: mockRequests,
        selectedIds: ["1", "3"],
      }),
    );

    const menuItems = result.current.bulkActionMenuItems;

    expect(menuItems).toHaveLength(5);
    expect(menuItems[0]).toMatchObject({
      key: BulkActionType.APPROVE,
      label: "Approve",
      disabled: false,
    });
    expect(menuItems[1]).toMatchObject({
      key: BulkActionType.DENY,
      label: "Deny",
      disabled: false,
    });
    expect(menuItems[2]).toMatchObject({
      key: BulkActionType.FINALIZE,
      label: "Finalize",
      disabled: true, // No requests in REQUIRES_MANUAL_FINALIZATION status
    });
    expect(menuItems[4]).toMatchObject({
      key: BulkActionType.DELETE,
      label: "Delete",
      disabled: false,
      danger: true,
    });
  });

  it("enables finalize action when requests require manual finalization", () => {
    const { result } = renderHook(() =>
      usePrivacyRequestBulkActions({
        requests: [requiresFinalizationRequest],
        selectedIds: ["4"],
      }),
    );

    const menuItems = result.current.bulkActionMenuItems;

    expect(menuItems[2]).toMatchObject({
      key: BulkActionType.FINALIZE,
      label: "Finalize",
      disabled: false,
    });
  });

  describe("Bulk actions", () => {
    it("approve: shows confirmation modal and calls API successfully", async () => {
      mockBulkApproveRequest.mockResolvedValue({
        data: {
          succeeded: [{ id: "1" }, { id: "2" }],
          failed: [],
        },
      });

      const { result } = renderHook(() =>
        usePrivacyRequestBulkActions({
          requests: [pendingRequest1, pendingRequest2],
          selectedIds: ["1", "2"],
        }),
      );

      const approveMenuItem = result.current.bulkActionMenuItems[0] as Extract<
        MenuProps["items"],
        Array<any>
      >[number] & { onClick?: (e: any) => void };

      await act(async () => {
        approveMenuItem?.onClick?.({} as any);
      });

      expect(mockModalApi.confirm).toHaveBeenCalledWith(
        expect.objectContaining({
          title: "Approve privacy requests",
          content:
            "You are about to approve 2 privacy requests. Are you sure you want to continue?",
        }),
      );

      const confirmCall = mockModalApi.confirm.mock.calls[0][0];
      await act(async () => {
        await confirmCall.onOk();
      });

      expect(mockBulkApproveRequest).toHaveBeenCalledWith({
        request_ids: ["1", "2"],
      });
    });

    it("delete: shows confirmation modal with danger type and calls API successfully", async () => {
      mockBulkSoftDeleteRequest.mockResolvedValue({
        data: {
          succeeded: [{ id: "1" }, { id: "2" }],
          failed: [],
        },
      });

      const { result } = renderHook(() =>
        usePrivacyRequestBulkActions({
          requests: [pendingRequest1, pendingRequest2],
          selectedIds: ["1", "2"],
        }),
      );

      const deleteMenuItem = result.current.bulkActionMenuItems[4] as Extract<
        MenuProps["items"],
        Array<any>
      >[number] & { onClick?: (e: any) => void };

      await act(async () => {
        deleteMenuItem?.onClick?.({} as any);
      });

      expect(mockModalApi.confirm).toHaveBeenCalledWith(
        expect.objectContaining({
          title: "Delete privacy requests",
          okType: "danger",
        }),
      );

      const confirmCall = mockModalApi.confirm.mock.calls[0][0];
      await act(async () => {
        await confirmCall.onOk();
      });

      expect(mockBulkSoftDeleteRequest).toHaveBeenCalledWith({
        request_ids: ["1", "2"],
      });
    });

    it("finalize: shows confirmation modal and calls API successfully", async () => {
      mockBulkFinalizeRequest.mockResolvedValue({
        data: {
          succeeded: [{ id: "4" }],
          failed: [],
        },
      });

      const { result } = renderHook(() =>
        usePrivacyRequestBulkActions({
          requests: [requiresFinalizationRequest],
          selectedIds: ["4"],
        }),
      );

      const finalizeMenuItem = result.current.bulkActionMenuItems[2] as Extract<
        MenuProps["items"],
        Array<any>
      >[number] & { onClick?: (e: any) => void };

      await act(async () => {
        finalizeMenuItem?.onClick?.({} as any);
      });

      expect(mockModalApi.confirm).toHaveBeenCalledWith(
        expect.objectContaining({
          title: "Finalize privacy requests",
          content:
            "You are about to finalize 1 privacy request. Are you sure you want to continue?",
        }),
      );

      const confirmCall = mockModalApi.confirm.mock.calls[0][0];
      await act(async () => {
        await confirmCall.onOk();
      });

      expect(mockBulkFinalizeRequest).toHaveBeenCalledWith({
        request_ids: ["4"],
      });
    });

    it("deny: calls API with reason and passes warning message for partial support", async () => {
      mockOpenDenyPrivacyRequestModal.mockResolvedValue(
        "User requested withdrawal",
      );
      mockBulkDenyRequest.mockResolvedValue({
        data: {
          succeeded: [{ id: "1" }],
          failed: [],
        },
      });

      const { result } = renderHook(() =>
        usePrivacyRequestBulkActions({
          requests: [pendingRequest1, completeRequest],
          selectedIds: ["1", "3"],
        }),
      );

      const denyMenuItem = result.current.bulkActionMenuItems[1] as Extract<
        MenuProps["items"],
        Array<any>
      >[number] & { onClick?: (e: any) => void };

      await act(async () => {
        await denyMenuItem?.onClick?.({} as any);
      });

      expect(mockOpenDenyPrivacyRequestModal).toHaveBeenCalledWith(
        "You have selected 2 requests, but only 1 request can perform this action. If you continue, the bulk action will only be applied to 1 request.",
      );
      expect(mockBulkDenyRequest).toHaveBeenCalledWith({
        request_ids: ["1"],
        reason: "User requested withdrawal",
      });
    });

    it("shows warning when only partial requests support the action", async () => {
      mockBulkApproveRequest.mockResolvedValue({
        data: {
          succeeded: [{ id: "1" }],
          failed: [],
        },
      });

      const { result } = renderHook(() =>
        usePrivacyRequestBulkActions({
          requests: [pendingRequest1, completeRequest],
          selectedIds: ["1", "3"],
        }),
      );

      const approveMenuItem = result.current.bulkActionMenuItems[0] as Extract<
        MenuProps["items"],
        Array<any>
      >[number] & { onClick?: (e: any) => void };

      await act(async () => {
        approveMenuItem?.onClick?.({} as any);
      });

      expect(mockModalApi.confirm).toHaveBeenCalledWith(
        expect.objectContaining({
          content:
            "You have selected 2 requests, but only 1 request can perform this action. If you continue, the bulk action will only be applied to 1 request.",
        }),
      );

      const confirmCall = mockModalApi.confirm.mock.calls[0][0];
      await act(async () => {
        await confirmCall.onOk();
      });

      expect(mockBulkApproveRequest).toHaveBeenCalledWith({
        request_ids: ["1"],
      });
    });

    it("does not call API when user cancels modal", async () => {
      const { result } = renderHook(() =>
        usePrivacyRequestBulkActions({
          requests: [pendingRequest1],
          selectedIds: ["1"],
        }),
      );

      const approveMenuItem = result.current.bulkActionMenuItems[0] as Extract<
        MenuProps["items"],
        Array<any>
      >[number] & { onClick?: (e: any) => void };

      await act(async () => {
        approveMenuItem?.onClick?.({} as any);
      });

      expect(mockModalApi.confirm).toHaveBeenCalled();
      expect(mockBulkApproveRequest).not.toHaveBeenCalled();
    });

    it("does not call API when user cancels deny modal", async () => {
      mockOpenDenyPrivacyRequestModal.mockResolvedValue(null);

      const { result } = renderHook(() =>
        usePrivacyRequestBulkActions({
          requests: [pendingRequest1],
          selectedIds: ["1"],
        }),
      );

      const denyMenuItem = result.current.bulkActionMenuItems[1] as Extract<
        MenuProps["items"],
        Array<any>
      >[number] & { onClick?: (e: any) => void };

      await act(async () => {
        await denyMenuItem?.onClick?.({} as any);
      });

      expect(mockOpenDenyPrivacyRequestModal).toHaveBeenCalled();
      expect(mockBulkDenyRequest).not.toHaveBeenCalled();
    });
  });
});
