import { act, renderHook } from "@testing-library/react";
import { AntMenuProps as MenuProps } from "fidesui";

import { PrivacyRequestStatus } from "~/types/api";

import { BulkActionType } from "../../helpers";
import { PrivacyRequestEntity } from "../../types";
import { usePrivacyRequestBulkActions } from "./usePrivacyRequestBulkActions";

const mockBulkApproveRequest = jest.fn();
const mockBulkDenyRequest = jest.fn();
const mockBulkSoftDeleteRequest = jest.fn();
const mockOpenDenyPrivacyRequestModal = jest.fn();

jest.mock("../../privacy-requests.slice", () => ({
  useBulkApproveRequestMutation: () => [mockBulkApproveRequest],
  useBulkDenyRequestMutation: () => [mockBulkDenyRequest],
  useBulkSoftDeleteRequestMutation: () => [mockBulkSoftDeleteRequest],
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
} as any;

const mockModalApi = {
  confirm: jest.fn(),
  info: jest.fn(),
  success: jest.fn(),
  error: jest.fn(),
  warning: jest.fn(),
} as any;

describe("usePrivacyRequestBulkActions", () => {
  // Shared test data
  const pendingRequest1: PrivacyRequestEntity = {
    id: "1",
    status: PrivacyRequestStatus.PENDING,
  } as PrivacyRequestEntity;

  const pendingRequest2: PrivacyRequestEntity = {
    id: "2",
    status: PrivacyRequestStatus.PENDING,
  } as PrivacyRequestEntity;

  const completeRequest: PrivacyRequestEntity = {
    id: "3",
    status: PrivacyRequestStatus.COMPLETE,
  } as PrivacyRequestEntity;

  const mockRequests: PrivacyRequestEntity[] = [
    pendingRequest1,
    completeRequest,
  ];
  const mockClearSelectedIds = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("returns correct menu items with proper disabled states", () => {
    const { result } = renderHook(() =>
      usePrivacyRequestBulkActions({
        requests: mockRequests,
        selectedIds: ["1", "3"],
        clearSelectedIds: mockClearSelectedIds,
        messageApi: mockMessageApi,
        modalApi: mockModalApi,
      }),
    );

    const menuItems = result.current.bulkActionMenuItems;

    expect(menuItems).toHaveLength(4);
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
    expect(menuItems[3]).toMatchObject({
      key: BulkActionType.DELETE,
      label: "Delete",
      disabled: false,
      danger: true,
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
          clearSelectedIds: mockClearSelectedIds,
          messageApi: mockMessageApi,
          modalApi: mockModalApi,
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
      expect(mockMessageApi.success).toHaveBeenCalledWith(
        "Successfully approved 2 privacy requests",
        5,
      );
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
          clearSelectedIds: mockClearSelectedIds,
          messageApi: mockMessageApi,
          modalApi: mockModalApi,
        }),
      );

      const deleteMenuItem = result.current.bulkActionMenuItems[3] as Extract<
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
      expect(mockMessageApi.success).toHaveBeenCalledWith(
        "Successfully deleted 2 privacy requests",
        5,
      );
    });

    it("deny: calls API with reason when user provides one", async () => {
      mockOpenDenyPrivacyRequestModal.mockResolvedValue(
        "User requested withdrawal",
      );
      mockBulkDenyRequest.mockResolvedValue({
        data: {
          succeeded: [{ id: "1" }, { id: "2" }],
          failed: [],
        },
      });

      const { result } = renderHook(() =>
        usePrivacyRequestBulkActions({
          requests: [pendingRequest1, pendingRequest2],
          selectedIds: ["1", "2"],
          clearSelectedIds: mockClearSelectedIds,
          messageApi: mockMessageApi,
          modalApi: mockModalApi,
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
      expect(mockBulkDenyRequest).toHaveBeenCalledWith({
        request_ids: ["1", "2"],
        reason: "User requested withdrawal",
      });
      expect(mockMessageApi.success).toHaveBeenCalledWith(
        "Successfully denied 2 privacy requests",
        5,
      );
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
          clearSelectedIds: mockClearSelectedIds,
          messageApi: mockMessageApi,
          modalApi: mockModalApi,
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
          clearSelectedIds: mockClearSelectedIds,
          messageApi: mockMessageApi,
          modalApi: mockModalApi,
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
          clearSelectedIds: mockClearSelectedIds,
          messageApi: mockMessageApi,
          modalApi: mockModalApi,
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
