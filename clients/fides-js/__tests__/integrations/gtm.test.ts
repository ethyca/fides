import { FidesEventType } from "../../src/docs";
import { gtm } from "../../src/integrations/gtm";

const fidesEvents: Record<FidesEventType, true> = {
  FidesInitializing: true,
  FidesInitialized: true,
  FidesUpdating: true,
  FidesUpdated: true,
  FidesUIChanged: true,
  FidesUIShown: true,
  FidesModalClosed: true,
};
const events = Object.keys(fidesEvents) as FidesEventType[];

describe("gtm", () => {
  afterEach(() => {
    window.dataLayer = undefined;
  });

  test.each(events)("that fides forwards all %s event to gtm", (eventName) => {
    gtm();
    window.dispatchEvent(
      new CustomEvent(eventName, { detail: { consent: {} } }),
    );
    expect(
      window.dataLayer?.filter((event) => event.event === eventName).length,
    ).toBeGreaterThanOrEqual(1);
  });
});
