import { FidesEventType } from "../../src/docs";
import { gtm } from "../../src/integrations/gtm";

const fidesEvents: Record<FidesEventType, boolean> = {
  FidesInitializing: false,
  FidesInitialized: true,
  FidesUpdating: true,
  FidesUpdated: true,
  FidesUIChanged: true,
  FidesUIShown: true,
  FidesModalClosed: true,
};
const eventsThatFire = Object.entries(fidesEvents).filter(
  ([, dispatchToGtm]) => dispatchToGtm,
);
const eventsThatDoNotFire = Object.entries(fidesEvents).filter(
  ([, dispatchToGtm]) => !dispatchToGtm,
);

describe("gtm", () => {
  afterEach(() => {
    window.dataLayer = undefined;
  });

  test.each(eventsThatFire)(
    "that fides forwards %s event to gtm if appropriate",
    (eventName) => {
      gtm();
      window.dispatchEvent(
        new CustomEvent(eventName, { detail: { consent: {} } }),
      );

      expect(
        (window.dataLayer ?? []).filter((event) => event.event === eventName)
          .length,
      ).toBeGreaterThanOrEqual(1);
    },
  );

  test.each(eventsThatDoNotFire)(
    "that fides doesn't forward %s event to gtm",
    (eventName) => {
      gtm();
      window.dispatchEvent(
        new CustomEvent(eventName, { detail: { consent: {} } }),
      );

      expect(
        (window.dataLayer ?? []).filter((event) => event.event === eventName)
          .length,
      ).toBeLessThan(1);
    },
  );

  test("that fides transforms consent values to strings when asStringValues is true", () => {
    // Mock the privacy notices
    window.Fides = {
      experience: {
        privacy_notices: [
          {
            notice_key: "test_notice_1",
            consent_mechanism: "opt_in",
          },
          {
            notice_key: "test_notice_2",
            consent_mechanism: "opt_out",
          },
          {
            notice_key: "test_notice_3",
            consent_mechanism: "notice_only",
          },
        ],
      } as any,
    } as any;

    gtm({ asStringValues: true });
    window.dispatchEvent(
      new CustomEvent("FidesUpdated", {
        detail: {
          consent: {
            test_notice_1: true,
            test_notice_2: false,
            test_notice_3: true,
          },
        },
      }),
    );

    const fidesEvent = window.dataLayer?.[window.dataLayer.length - 1];

    expect(fidesEvent?.Fides.consent.test_notice_1).toBe("opt_in");
    expect(fidesEvent?.Fides.consent.test_notice_2).toBe("opt_out");
    expect(fidesEvent?.Fides.consent.test_notice_3).toBe("acknowledge");
  });

  test("that fides includes not applicable privacy notices when includeNotApplicable is true", () => {
    window.Fides = {
      experience: {
        privacy_notices: [
          {
            notice_key: "test_notice_1",
            consent_mechanism: "opt_in",
          },
          {
            notice_key: "test_notice_2",
            consent_mechanism: "opt_out",
          },
          {
            notice_key: "test_notice_3",
            consent_mechanism: "notice_only",
          },
        ],
        non_applicable_privacy_notices: ["na_notice_1", "na_notice_2"],
      } as any,
    } as any;

    gtm({ includeNotApplicable: true });
    window.dispatchEvent(
      new CustomEvent("FidesUpdated", {
        detail: {
          consent: {
            test_notice_1: true,
            test_notice_2: false,
            test_notice_3: true,
          },
        },
      }),
    );

    const fidesEvent = window.dataLayer?.[window.dataLayer.length - 1];

    expect(fidesEvent?.Fides.consent.na_notice_1).toBe(false);
    expect(fidesEvent?.Fides.consent.na_notice_2).toBe(false);
  });

  test("that fides includes not applicable privacy notices and transforms them to strings", () => {
    gtm({ includeNotApplicable: true });
    window.Fides = {
      experience: {
        privacy_notices: [
          {
            notice_key: "test_notice_1",
            consent_mechanism: "opt_in",
          },
          {
            notice_key: "test_notice_2",
            consent_mechanism: "opt_out",
          },
          {
            notice_key: "test_notice_3",
            consent_mechanism: "notice_only",
          },
        ],
        non_applicable_privacy_notices: ["na_notice_1", "na_notice_2"],
      } as any,
    } as any;

    gtm({ includeNotApplicable: true, asStringValues: true });
    window.dispatchEvent(
      new CustomEvent("FidesUpdated", {
        detail: {
          consent: {
            test_notice_1: true,
            test_notice_2: false,
            test_notice_3: true,
          },
        },
      }),
    );

    const fidesEvent = window.dataLayer?.[window.dataLayer.length - 1];

    expect(fidesEvent?.Fides.consent.na_notice_1).toBe("not_applicable");
    expect(fidesEvent?.Fides.consent.na_notice_2).toBe("not_applicable");
  });
});
