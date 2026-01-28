import { PrivacyRequestResponse, PrivacyRequestStatus } from "~/types/api";

import {
  BulkActionType,
  getAvailableActionsForRequest,
  isActionSupportedByRequests,
} from "./helpers";

describe("helpers", () => {
  describe("BulkActionType", () => {
    it("should include FINALIZE action type", () => {
      expect(BulkActionType.FINALIZE).toBe("finalize");
    });
  });

  describe("getAvailableActionsForRequest", () => {
    it("returns approve, deny, and delete for pending requests", () => {
      const request = {
        status: PrivacyRequestStatus.PENDING,
      } as PrivacyRequestResponse;

      const actions = getAvailableActionsForRequest(request);

      expect(actions).toContain(BulkActionType.APPROVE);
      expect(actions).toContain(BulkActionType.DENY);
      expect(actions).toContain(BulkActionType.DELETE);
      expect(actions).not.toContain(BulkActionType.FINALIZE);
    });

    it("returns finalize and delete for requests requiring manual finalization", () => {
      const request = {
        status: PrivacyRequestStatus.REQUIRES_MANUAL_FINALIZATION,
      } as PrivacyRequestResponse;

      const actions = getAvailableActionsForRequest(request);

      expect(actions).toContain(BulkActionType.FINALIZE);
      expect(actions).toContain(BulkActionType.DELETE);
      expect(actions).not.toContain(BulkActionType.APPROVE);
      expect(actions).not.toContain(BulkActionType.DENY);
    });

    it("returns only delete for complete requests", () => {
      const request = {
        status: PrivacyRequestStatus.COMPLETE,
      } as PrivacyRequestResponse;

      const actions = getAvailableActionsForRequest(request);

      expect(actions).toEqual([BulkActionType.DELETE]);
    });
  });

  describe("isActionSupportedByRequests", () => {
    it("returns true if at least one request supports finalize", () => {
      const requests = [
        { status: PrivacyRequestStatus.PENDING } as PrivacyRequestResponse,
        {
          status: PrivacyRequestStatus.REQUIRES_MANUAL_FINALIZATION,
        } as PrivacyRequestResponse,
      ];

      expect(
        isActionSupportedByRequests(BulkActionType.FINALIZE, requests),
      ).toBe(true);
    });

    it("returns false if no requests support finalize", () => {
      const requests = [
        { status: PrivacyRequestStatus.PENDING } as PrivacyRequestResponse,
        { status: PrivacyRequestStatus.COMPLETE } as PrivacyRequestResponse,
      ];

      expect(
        isActionSupportedByRequests(BulkActionType.FINALIZE, requests),
      ).toBe(false);
    });

    it("returns true for approve when pending requests exist", () => {
      const requests = [
        { status: PrivacyRequestStatus.PENDING } as PrivacyRequestResponse,
        {
          status: PrivacyRequestStatus.REQUIRES_MANUAL_FINALIZATION,
        } as PrivacyRequestResponse,
      ];

      expect(
        isActionSupportedByRequests(BulkActionType.APPROVE, requests),
      ).toBe(true);
    });

    it("returns true for delete for any request status", () => {
      const requests = [
        { status: PrivacyRequestStatus.COMPLETE } as PrivacyRequestResponse,
        {
          status: PrivacyRequestStatus.REQUIRES_MANUAL_FINALIZATION,
        } as PrivacyRequestResponse,
      ];

      expect(isActionSupportedByRequests(BulkActionType.DELETE, requests)).toBe(
        true,
      );
    });
  });
});
