import { FidesGlobal } from "../../src/fides";
import { blueconic } from "../../src/integrations/blueconic";
import { UserGeolocation } from "fides-js";
import { MARKETING_CONSENT_KEYS } from "../../src/lib/consent-constants";

const getBlueConicEvent = () =>
  ({
    subscribe: () => { },
  }) as const;

const setupBlueConicClient = (
  initialized: "initialized" | "uinitialized" = "initialized",
) => {
  const mockProfile = {
    setConsentedObjectives: jest.fn(),
    setRefusedObjectives: jest.fn(),
    setValue: jest.fn(),
  };
  const client = {
    profile: {
      getProfile: jest.fn(() => mockProfile),
      updateProfile: jest.fn(),
    },
    event: initialized === "initialized" ? getBlueConicEvent() : undefined,
  } as const satisfies typeof window.blueConicClient;

  window.blueConicClient = client;

  return { client, mockProfile };
};

const setupFidesWithConsent = (key: string, optInStatus: boolean) => {
  window.Fides = {
    consent: {
      [key]: optInStatus,
    },
  } as any as FidesGlobal;
};

const setupFidesWithoutConsent = () => {
  window.Fides = {
    consent: {},
  } as any as FidesGlobal;
};

const setupFidesWithGeoLocationAndFidesUser = (
  fidesUserId: string,
  geolocation: UserGeolocation,
) => {
  window.Fides = {
    consent: {},
    identity: { "fides_user_device_id": fidesUserId },
    geolocation: geolocation,
  } as any as FidesGlobal;
};

describe("blueconic", () => {
  afterEach(() => {
    window.blueConicClient = undefined;
    window.Fides = undefined as any;
    jest.resetAllMocks();
  });

  describe("approaches", () => {
    test("that other approaches are not supported", () => {
      expect(() =>
        blueconic({ approach: "other mode" as "onetrust" }),
      ).toThrow();
    });

    describe.each([undefined, "onetrust"] as const)(
      "onetrust approach",
      (approach) => {
        test("when fides configures no consent, blueconic sets consent for all purposes", () => {
          const { client, mockProfile } = setupBlueConicClient();
          setupFidesWithoutConsent();

          blueconic({ approach });

          expect(mockProfile.setConsentedObjectives).toHaveBeenCalledWith([
            "iab_purpose_1",
            "iab_purpose_2",
            "iab_purpose_3",
            "iab_purpose_4",
          ]);
          expect(mockProfile.setRefusedObjectives).toHaveBeenCalledWith([]);
          expect(client.profile.updateProfile).toHaveBeenCalled();
        });

        describe.each(MARKETING_CONSENT_KEYS)(
          "when consent is set via the %s key",
          (key) => {
            test.each([
              [
                "opted in",
                true,
                [
                  "iab_purpose_1",
                  "iab_purpose_2",
                  "iab_purpose_3",
                  "iab_purpose_4",
                ],
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
                const { client, mockProfile } = setupBlueConicClient();
                setupFidesWithConsent(key, optInStatus);

                blueconic();

                expect(mockProfile.setConsentedObjectives).toHaveBeenCalledWith(
                  consented,
                );
                expect(mockProfile.setRefusedObjectives).toHaveBeenCalledWith(
                  refused,
                );
                expect(client.profile.updateProfile).toHaveBeenCalled();
              },
            );
          },
        );
      },
    );
  });

  test("that nothing happens when blueconic and fides are not initialized", () => {
    const { mockProfile } = setupBlueConicClient("uinitialized");

    blueconic();

    expect(mockProfile.setConsentedObjectives).not.toHaveBeenCalled();
    expect(mockProfile.setRefusedObjectives).not.toHaveBeenCalled();
    expect(
      window.blueConicClient?.profile?.updateProfile,
    ).not.toHaveBeenCalled();
  });

  test("that geolocation gets assigned to BlueConic profile", () => {
    const { mockProfile } = setupBlueConicClient("initialized");

    const fidesUserId = "b020c053-0ea2-409c-b71c-a55b6236f842";
    const fides_geolocation = {
      location: "US-NY",
      country: "US",
      region: "NY",
    };

    setupFidesWithGeoLocationAndFidesUser(fidesUserId, fides_geolocation);

    blueconic();

    expect(mockProfile.setValue).toHaveBeenCalledWith(
      "fides_identifier", fidesUserId
    );
    expect(mockProfile.setValue).toHaveBeenCalledWith(
      "fides_geolocation", fides_geolocation
    );
    expect(window.blueConicClient?.profile?.updateProfile).toHaveBeenCalled();
  });

  test.each(["FidesInitialized", "FidesUpdated", "onBlueConicLoaded"])(
    "that %s event can cause objectives to be set",
    (eventName) => {
      const spy = jest.spyOn(window, "addEventListener");
      blueconic();
      expect(spy).toHaveBeenCalledWith(eventName, expect.any(Function));
    },
  );
});
