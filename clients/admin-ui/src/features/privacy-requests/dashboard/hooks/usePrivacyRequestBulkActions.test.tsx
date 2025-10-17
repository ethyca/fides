import { renderHook } from "@testing-library/react";

import { PrivacyRequestStatus } from "~/types/api";

import { BulkActionType } from "../../helpers";
import { PrivacyRequestEntity } from "../../types";
import { usePrivacyRequestBulkActions } from "./usePrivacyRequestBulkActions";

const mockBulkApproveRequest = jest.fn();
const mockBulkDenyRequest = jest.fn();
const mockBulkSoftDeleteRequest = jest.fn();

jest.mock("../../privacy-requests.slice", () => ({
  useBulkApproveRequestMutation: () => [mockBulkApproveRequest],
  useBulkDenyRequestMutation: () => [mockBulkDenyRequest],
  useBulkSoftDeleteRequestMutation: () => [mockBulkSoftDeleteRequest],
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
  const mockRequests: PrivacyRequestEntity[] = [
    { id: "1", status: PrivacyRequestStatus.PENDING } as PrivacyRequestEntity,
    { id: "2", status: PrivacyRequestStatus.COMPLETE } as PrivacyRequestEntity,
  ];
  const mockClearSelectedIds = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("returns correct menu items with proper disabled states", () => {
    const { result } = renderHook(() =>
      usePrivacyRequestBulkActions({
        requests: mockRequests,
        selectedIds: ["1", "2"],
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

  // TODO: Test for the actions will be added in a later PR together with confirmation modals
});
