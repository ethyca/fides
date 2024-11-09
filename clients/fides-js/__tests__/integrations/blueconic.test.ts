import { FidesGlobal } from "../../src/fides";
import { blueconic } from "../../src/integrations/blueconic";
import { MARKETING_CONSENT_KEYS } from "../../src/lib/consent-constants";

const getBlueConicEvent = () =>
  ({
    subscribe: () => {},
  }) as const;

const setupBlueConicClient = (
  initialized: "initialized" | "uinitialized" = "initialized",
) => {
  const client = {
    profile: {
      setConsentedObjectives: jest.fn(),
      setRefusedObjectives: jest.fn(),
      updateProfile: jest.fn(),
    },
    event: initialized === "initialized" ? getBlueConicEvent() : undefined,
  } as const satisfies typeof window.blueConicClient;

  window.blueConicClient = client;

  return client;
};

const setupFidesWithConsent = (key: string, optInStatus: boolean) => {
  window.Fides = {
    consent: {
      [key]: optInStatus,
    },
  } as any as FidesGlobal;
};

describe("blueconic", () => {
  afterEach(() => {
    window.blueConicClient = undefined;
    window.Fides = undefined as any;
    jest.resetAllMocks();
  });

  test("that other modes are not supported", () => {
    expect(() => blueconic({ approach: "other mode" as "onetrust" })).toThrow();
  });

  test("that nothing happens when blueconic and fides are not initialized", () => {
    setupBlueConicClient("uinitialized");

    blueconic();

    expect(
      window.blueConicClient?.profile?.setConsentedObjectives,
    ).not.toHaveBeenCalled();
    expect(
      window.blueConicClient?.profile?.setConsentedObjectives,
    ).not.toHaveBeenCalled();
    expect(
      window.blueConicClient?.profile?.updateProfile,
    ).not.toHaveBeenCalled();
  });

  describe.each(MARKETING_CONSENT_KEYS)(
    "when consent is set via the %s key",
    (key) => {
      test.each([
        [
          "opted in",
          true,
          ["iab_purpose_1", "iab_purpose_2", "iab_purpose_3", "iab_purpose_4"],
          [],
        ],
        [
          "opted out",
          false,
          ["iab_purpose_1"],
          ["iab_purpose_2", "iab_purpose_3", "iab_purpose_4"],
        ],
      ])(
        "that a user who has %s gets the correct consented and refused objectives",
        (_, optInStatus, consented, refused) => {
          const blueConicClient = setupBlueConicClient();
          setupFidesWithConsent(key, optInStatus);

          blueconic();

          expect(
            blueConicClient.profile.setConsentedObjectives,
          ).toHaveBeenCalledWith(consented);
          expect(
            blueConicClient.profile.setRefusedObjectives,
          ).toHaveBeenCalledWith(refused);
          expect(blueConicClient.profile.updateProfile).toHaveBeenCalled();
        },
      );
    },
  );

  test.each(["FidesInitialized", "FidesUpdated", "onBlueConicLoaded"])(
    "that %s event can cause objectives to be set",
    (eventName) => {
      const spy = jest.spyOn(window, "addEventListener");
      blueconic();
      expect(spy).toHaveBeenCalledWith(eventName, expect.any(Function));
    },
  );
});
