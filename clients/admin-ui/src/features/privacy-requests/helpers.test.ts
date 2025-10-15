import { PrivacyRequestStatus } from "~/types/api";

import {
  BulkActionType,
  getAvailableActionsForRequest,
  isActionSupportedByRequests,
} from "./helpers";
import { PrivacyRequestEntity } from "./types";

// Helper to create a mock privacy request
const createMockRequest = (
  status: PrivacyRequestStatus,
): PrivacyRequestEntity =>
  ({
    id: "test-id",
    status,
    identity: {},
    policy: {
      name: "Test Policy",
      key: "test-policy",
      rules: [],
    },
    created_at: "2024-01-01T00:00:00Z",
  }) as PrivacyRequestEntity;

describe("getAvailableActionsForRequest", () => {
  it("should return approve and deny for pending requests", () => {
    const request = createMockRequest(PrivacyRequestStatus.PENDING);
    const actions = getAvailableActionsForRequest(request);

    expect(actions).toContain(BulkActionType.APPROVE);
    expect(actions).toContain(BulkActionType.DENY);
    expect(actions).toContain(BulkActionType.DELETE);
    expect(actions).not.toContain(BulkActionType.FINALIZE);
  });

  it("should return finalize for requests requiring manual finalization", () => {
    const request = createMockRequest(
      PrivacyRequestStatus.REQUIRES_MANUAL_FINALIZATION,
    );
    const actions = getAvailableActionsForRequest(request);

    expect(actions).toContain(BulkActionType.FINALIZE);
    expect(actions).toContain(BulkActionType.DELETE);
    expect(actions).not.toContain(BulkActionType.APPROVE);
    expect(actions).not.toContain(BulkActionType.DENY);
  });

  it("should only return delete for completed requests", () => {
    const request = createMockRequest(PrivacyRequestStatus.COMPLETE);
    const actions = getAvailableActionsForRequest(request);

    expect(actions).toEqual([BulkActionType.DELETE]);
  });

  it("should only return delete for approved requests", () => {
    const request = createMockRequest(PrivacyRequestStatus.APPROVED);
    const actions = getAvailableActionsForRequest(request);

    expect(actions).toEqual([BulkActionType.DELETE]);
  });

  it("should only return delete for denied requests", () => {
    const request = createMockRequest(PrivacyRequestStatus.DENIED);
    const actions = getAvailableActionsForRequest(request);

    expect(actions).toEqual([BulkActionType.DELETE]);
  });

  it("should only return delete for error requests", () => {
    const request = createMockRequest(PrivacyRequestStatus.ERROR);
    const actions = getAvailableActionsForRequest(request);

    expect(actions).toEqual([BulkActionType.DELETE]);
  });
});

describe("isActionSupportedByRequests", () => {
  it("should return true if at least one request supports the action", () => {
    const requests = [
      createMockRequest(PrivacyRequestStatus.PENDING),
      createMockRequest(PrivacyRequestStatus.COMPLETE),
      createMockRequest(PrivacyRequestStatus.ERROR),
    ];

    expect(isActionSupportedByRequests(BulkActionType.APPROVE, requests)).toBe(
      true,
    );
    expect(isActionSupportedByRequests(BulkActionType.DENY, requests)).toBe(
      true,
    );
  });

  it("should return false if no requests support the action", () => {
    const requests = [
      createMockRequest(PrivacyRequestStatus.COMPLETE),
      createMockRequest(PrivacyRequestStatus.ERROR),
    ];

    expect(isActionSupportedByRequests(BulkActionType.APPROVE, requests)).toBe(
      false,
    );
    expect(isActionSupportedByRequests(BulkActionType.DENY, requests)).toBe(
      false,
    );
  });

  it("should return true for delete action with any request", () => {
    const requests = [
      createMockRequest(PrivacyRequestStatus.PENDING),
      createMockRequest(PrivacyRequestStatus.COMPLETE),
      createMockRequest(PrivacyRequestStatus.ERROR),
    ];

    expect(isActionSupportedByRequests(BulkActionType.DELETE, requests)).toBe(
      true,
    );
  });

  it("should return true for finalize when at least one request requires manual finalization", () => {
    const requests = [
      createMockRequest(PrivacyRequestStatus.PENDING),
      createMockRequest(PrivacyRequestStatus.REQUIRES_MANUAL_FINALIZATION),
      createMockRequest(PrivacyRequestStatus.COMPLETE),
    ];

    expect(isActionSupportedByRequests(BulkActionType.FINALIZE, requests)).toBe(
      true,
    );
  });

  it("should return false for finalize when no requests require manual finalization", () => {
    const requests = [
      createMockRequest(PrivacyRequestStatus.PENDING),
      createMockRequest(PrivacyRequestStatus.COMPLETE),
    ];

    expect(isActionSupportedByRequests(BulkActionType.FINALIZE, requests)).toBe(
      false,
    );
  });

  it("should handle empty request array", () => {
    const requests: PrivacyRequestEntity[] = [];

    expect(isActionSupportedByRequests(BulkActionType.APPROVE, requests)).toBe(
      false,
    );
    expect(isActionSupportedByRequests(BulkActionType.DENY, requests)).toBe(
      false,
    );
    expect(isActionSupportedByRequests(BulkActionType.FINALIZE, requests)).toBe(
      false,
    );
    expect(isActionSupportedByRequests(BulkActionType.DELETE, requests)).toBe(
      false,
    );
  });
});
