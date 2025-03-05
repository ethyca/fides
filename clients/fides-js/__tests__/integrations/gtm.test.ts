import { FidesEventType } from "../../src/docs";
import { gtm } from "../../src/integrations/gtm";

const fidesEvents: Record<FidesEventType, boolean> = {
  FidesInitializing: false,
  FidesInitialized: true,
  FidesUpdating: true,
  FidesUpdated: true,
  FidesUIChanged: true,
  FidesUIShown: false,
  FidesModalClosed: false,
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
});
