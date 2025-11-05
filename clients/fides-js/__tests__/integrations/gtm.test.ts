import { FidesEventType } from "../../src/docs";
import { gtm } from "../../src/integrations/gtm";
import {
  ConsentFlagType,
  ConsentNonApplicableFlagMode,
  FidesGlobal,
} from "../../src/lib/consent-types";

const fidesEvents: Record<
  FidesEventType,
  { forwardEvent: boolean; dispatchSynthetic: boolean }
> = {
  FidesInitializing: {
    forwardEvent: false,
    dispatchSynthetic: false,
  },
  FidesInitialized: {
    forwardEvent: true,
    dispatchSynthetic: true,
  },
  FidesConsentLoaded: {
    forwardEvent: true,
    dispatchSynthetic: false,
  },
  FidesReady: {
    forwardEvent: true,
    dispatchSynthetic: true,
  },
  FidesUpdating: {
    forwardEvent: true,
    dispatchSynthetic: false,
  },
  FidesUpdated: {
    forwardEvent: true,
    dispatchSynthetic: false,
  },
  FidesUIChanged: {
    forwardEvent: true,
    dispatchSynthetic: false,
  },
  FidesUIShown: {
    forwardEvent: true,
    dispatchSynthetic: false,
  },
  FidesModalClosed: {
    forwardEvent: true,
    dispatchSynthetic: false,
  },
};
const fidesEventsArray = Object.entries(fidesEvents);

const eventsThatAreForwarded = fidesEventsArray.filter(
  ([, { forwardEvent }]) => forwardEvent,
);
const eventsThatAreNotForwarded = fidesEventsArray.filter(
  ([, { forwardEvent }]) => !forwardEvent,
);
const eventsThatAreSyntheticallyDispatchedIfInitializationMissed =
  fidesEventsArray.filter(([, { dispatchSynthetic }]) => dispatchSynthetic);

describe("gtm", () => {
  afterEach(() => {
    window.dataLayer = undefined;
  });

  describe("Fides events", () => {
    test.each(eventsThatAreForwarded)(
      "fides forwards %s event to gtm if appropriate",
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

    test.each(eventsThatAreNotForwarded)(
      "fides doesn't forward %s event to gtm",
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

    describe.each(eventsThatAreSyntheticallyDispatchedIfInitializationMissed)(
      "for synthetic event %s",
      (eventName) => {
        beforeEach(() => {
          window.Fides = {} as FidesGlobal;
          window.Fides.initialized = true;
        });

        test("that fides fires the event if it was already initialized when gtm was called", () => {
          window.Fides.initialized = true;

          gtm();

          expect(
            (window.dataLayer ?? []).filter(
              (event) => event.event === eventName,
            ).length,
          ).toBe(1);
        });

        afterEach(() => {
          window.Fides = undefined as unknown as FidesGlobal;
        });
      },
    );
  });

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

    gtm({ flag_type: ConsentFlagType.CONSENT_MECHANISM });
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

    gtm({ non_applicable_flag_mode: ConsentNonApplicableFlagMode.INCLUDE });
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

    expect(fidesEvent?.Fides.consent.na_notice_1).toBe(true);
    expect(fidesEvent?.Fides.consent.na_notice_2).toBe(true);
  });

  test("that fides includes not applicable privacy notices and transforms them to strings", () => {
    gtm({ non_applicable_flag_mode: ConsentNonApplicableFlagMode.INCLUDE });
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

    gtm({
      non_applicable_flag_mode: ConsentNonApplicableFlagMode.INCLUDE,
      flag_type: ConsentFlagType.CONSENT_MECHANISM,
    });
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
