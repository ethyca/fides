import { PrivacyRequestResponse, PrivacyRequestStatus } from "~/types/api";

import {
  BulkActionType,
  getAvailableActionsForRequest,
  getButtonVisibility,
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

  describe("getButtonVisibility", () => {
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
      "Button visibility for $status",
      ({ status, approve, deny, finalize, delete: deleteBtn }) => {
        it("should return correct button visibility", () => {
          const visibility = getButtonVisibility(status);

          expect(visibility.approve).toBe(approve);
          expect(visibility.deny).toBe(deny);
          expect(visibility.finalize).toBe(finalize);
          expect(visibility.delete).toBe(deleteBtn);
        });
      },
    );
  });
});
