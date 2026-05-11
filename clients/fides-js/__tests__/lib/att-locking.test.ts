import {
  ConsentMechanism,
  FidesAttStatus,
  PrivacyNoticeWithPreference,
} from "~/lib/consent-types";
import { filterAttDeniedFromDraft } from "~/lib/tcf/att-utils";

const makeNotice = (
  overrides: Partial<PrivacyNoticeWithPreference> = {},
): PrivacyNoticeWithPreference =>
  ({
    id: "notice-1",
    notice_key: "analytics",
    consent_mechanism: ConsentMechanism.OPT_IN,
    att_exempt: false,
    ...overrides,
  }) as unknown as PrivacyNoticeWithPreference;

describe("filterAttDeniedFromDraft", () => {
  const draftIds = ["notice-1", "notice-2", "notice-3"];

  describe("when ATT is not denied", () => {
    it.each([
      FidesAttStatus.NOT_DETERMINED,
      FidesAttStatus.AUTHORIZED,
      undefined,
    ])("returns draft unchanged when fidesAttStatus is %s", (status) => {
      const notices = [makeNotice({ id: "notice-1" })];
      const result = filterAttDeniedFromDraft(draftIds, notices, status);
      expect(result).toEqual(draftIds);
    });
  });

  describe("when ATT is denied (status is 'denied' or 'restricted')", () => {
    it.each([FidesAttStatus.DENIED, FidesAttStatus.RESTRICTED])(
      "removes non-exempt notices from draft when status is %s",
      (status) => {
        const notices = [
          makeNotice({ id: "notice-1", att_exempt: false }),
          makeNotice({ id: "notice-2", att_exempt: false }),
          makeNotice({ id: "notice-3", att_exempt: false }),
        ];
        const result = filterAttDeniedFromDraft(draftIds, notices, status);
        expect(result).toEqual([]);
      },
    );

    it.each([FidesAttStatus.DENIED, FidesAttStatus.RESTRICTED])(
      "preserves att_exempt notices when status is %s",
      (status) => {
        const notices = [
          makeNotice({ id: "notice-1", att_exempt: true }),
          makeNotice({ id: "notice-2", att_exempt: false }),
          makeNotice({ id: "notice-3", att_exempt: true }),
        ];
        const result = filterAttDeniedFromDraft(draftIds, notices, status);
        expect(result).toEqual(["notice-1", "notice-3"]);
      },
    );

    it.each([FidesAttStatus.DENIED, FidesAttStatus.RESTRICTED])(
      "preserves notice_only notices regardless of att_exempt when status is %s",
      (status) => {
        const notices = [
          makeNotice({
            id: "notice-1",
            consent_mechanism: ConsentMechanism.NOTICE_ONLY,
            att_exempt: false,
          }),
          makeNotice({ id: "notice-2", att_exempt: false }),
        ];
        const result = filterAttDeniedFromDraft(
          ["notice-1", "notice-2"],
          notices,
          status,
        );
        expect(result).toEqual(["notice-1"]);
      },
    );

    it("handles IDs not found in the notices map (removes them)", () => {
      const notices = [makeNotice({ id: "notice-1", att_exempt: true })];
      const result = filterAttDeniedFromDraft(
        ["notice-1", "unknown-id"],
        notices,
        FidesAttStatus.DENIED,
      );
      // unknown-id has no notice entry → treated as non-exempt, removed
      expect(result).toEqual(["notice-1"]);
    });

    it("returns empty array when all notices are non-exempt and non-notice_only", () => {
      const notices = [
        makeNotice({ id: "notice-1", att_exempt: false }),
        makeNotice({ id: "notice-2", att_exempt: false }),
      ];
      const result = filterAttDeniedFromDraft(
        ["notice-1", "notice-2"],
        notices,
        FidesAttStatus.DENIED,
      );
      expect(result).toEqual([]);
    });
  });
});

describe("ATT locking: notice disabled logic", () => {
  /**
   * Tests for the inline disabled computation in TcfOverlay's
   * privacyNoticesWithBestTranslation memo. Since this logic is inline JSX,
   * we verify the boolean expression directly here.
   */
  const isAttLocked = (
    fidesAttStatus: FidesAttStatus | undefined,
    attExempt: boolean | undefined,
  ): boolean =>
    (fidesAttStatus === FidesAttStatus.DENIED ||
      fidesAttStatus === FidesAttStatus.RESTRICTED) &&
    !attExempt;

  it("does not lock notice when fidesAttStatus is not_determined", () => {
    expect(isAttLocked(FidesAttStatus.NOT_DETERMINED, false)).toBe(false);
    expect(isAttLocked(FidesAttStatus.NOT_DETERMINED, true)).toBe(false);
  });

  it("does not lock notice when fidesAttStatus is authorized", () => {
    expect(isAttLocked(FidesAttStatus.AUTHORIZED, false)).toBe(false);
    expect(isAttLocked(FidesAttStatus.AUTHORIZED, true)).toBe(false);
  });

  it("locks non-exempt notice when fidesAttStatus is denied", () => {
    expect(isAttLocked(FidesAttStatus.DENIED, false)).toBe(true);
    expect(isAttLocked(FidesAttStatus.DENIED, undefined)).toBe(true);
  });

  it("locks non-exempt notice when fidesAttStatus is restricted", () => {
    expect(isAttLocked(FidesAttStatus.RESTRICTED, false)).toBe(true);
    expect(isAttLocked(FidesAttStatus.RESTRICTED, undefined)).toBe(true);
  });

  it("does not lock att_exempt notice even when ATT is denied", () => {
    expect(isAttLocked(FidesAttStatus.DENIED, true)).toBe(false);
    expect(isAttLocked(FidesAttStatus.RESTRICTED, true)).toBe(false);
  });
});
