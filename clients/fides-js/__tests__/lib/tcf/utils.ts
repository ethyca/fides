import * as uuid from "uuid";

import { CookieAttributes } from "typescript-cookie/dist/types";
import { makeFidesCookie } from "~/lib/cookie";
import {
  TcfExperienceRecords,
  TCFPurposeConsentRecord,
  TCFVendorConsentRecord,
} from "~/lib/tcf/types";
import { updateExperienceFromCookieConsentTcf } from "~/lib/tcf/utils";
import { PrivacyExperience, UserConsentPreference } from "~/lib/consent-types";

// Setup mock date
const MOCK_DATE = "2023-01-01T12:00:00.000Z";
jest.useFakeTimers().setSystemTime(new Date(MOCK_DATE));

// Setup mock uuid
const MOCK_UUID = "fae7e16d-37fd-40ed-b2a8-a020ad90106d";
jest.mock("uuid");
const mockUuid = jest.mocked(uuid);
mockUuid.v4.mockReturnValue(MOCK_UUID);

// Setup mock typescript-cookie
// NOTE: the default module mocking just *doesn't* work for typescript-cookie
// for some mysterious reason (see note in jest.config.js), so we define a
// minimal mock implementation here
const mockGetCookie = jest.fn((): string | undefined => "mockGetCookie return");
const mockSetCookie = jest.fn(
  /* eslint-disable-next-line @typescript-eslint/no-unused-vars */
  (name: string, value: string, attributes: object, encoding: object) =>
    `mock setCookie return (value=${value})`
);
const mockRemoveCookie = jest.fn(
  /* eslint-disable-next-line @typescript-eslint/no-unused-vars */
  (name: string, attributes?: CookieAttributes) => undefined
);
jest.mock("typescript-cookie", () => ({
  getCookie: () => mockGetCookie(),
  setCookie: (
    name: string,
    value: string,
    attributes: object,
    encoding: object
  ) => mockSetCookie(name, value, attributes, encoding),
  removeCookie: (name: string, attributes?: CookieAttributes) =>
    mockRemoveCookie(name, attributes),
}));

describe("updateExperienceFromCookieConsentTcf", () => {
  const baseCookie = makeFidesCookie();

  // TCF test data
  const purposeRecords = [
    { id: 1 },
    { id: 2 },
    { id: 3 },
  ] as TCFPurposeConsentRecord[];
  const featureRecords = [
    { id: 4 },
    { id: 5 },
    { id: 6 },
  ] as TCFPurposeConsentRecord[];
  const vendorRecords = [
    { id: "1111" },
    { id: "ctl_test_system" },
  ] as TCFVendorConsentRecord[];
  const experienceWithTcf = {
    tcf_purpose_consents: purposeRecords,
    tcf_legitimate_interests_consent: purposeRecords,
    tcf_special_purposes: purposeRecords,
    tcf_features: featureRecords,
    tcf_special_features: featureRecords,
    tcf_vendor_consents: vendorRecords,
    tcf_vendor_legitimate_interests: vendorRecords,
    tcf_system_consents: vendorRecords,
    tcf_system_legitimate_interests: vendorRecords,
  } as unknown as PrivacyExperience;

  describe("tcf", () => {
    it("can handle an empty tcf cookie", () => {
      const updatedExperience = updateExperienceFromCookieConsentTcf({
        experience: experienceWithTcf,
        cookie: baseCookie,
      });
      expect(updatedExperience.tcf_purpose_consents).toEqual([
        { id: 1, current_preference: undefined },
        {
          id: 2,
          current_preference: undefined,
        },
        { id: 3, current_preference: undefined },
      ]);
    });

    it("can handle updating preferences", () => {
      const cookie = {
        ...baseCookie,
        tcf_consent: {
          system_consent_preferences: {
            1111: true,
            ctl_test_system: false,
          },
        },
      };
      const updatedExperience = updateExperienceFromCookieConsentTcf({
        experience: experienceWithTcf,
        cookie,
      });
      expect(updatedExperience.tcf_system_consents).toEqual([
        { id: "1111", current_preference: UserConsentPreference.OPT_IN },
        {
          id: "ctl_test_system",
          current_preference: UserConsentPreference.OPT_OUT,
        },
      ]);
      // The rest should be undefined
      const keys: Array<keyof TcfExperienceRecords> = [
        "tcf_purpose_legitimate_interests",
        "tcf_special_purposes",
        "tcf_features",
        "tcf_special_features",
        "tcf_vendor_consents",
        "tcf_purpose_consents",
        "tcf_vendor_legitimate_interests",
        "tcf_system_legitimate_interests",
      ];
      keys.forEach((key) => {
        updatedExperience[key]?.forEach((f) => {
          expect(f.current_preference).toEqual(undefined);
        });
      });
    });

    it("can handle when cookie has values not in the experience", () => {
      const cookie = {
        ...baseCookie,
        tcf_consent: {
          system_consent_preferences: {
            1111: false,
            2: false,
            555: false,
          },
        },
      };
      const updatedExperience = updateExperienceFromCookieConsentTcf({
        experience: experienceWithTcf,
        cookie,
      });
      expect(updatedExperience.tcf_system_consents).toEqual([
        { id: "1111", current_preference: UserConsentPreference.OPT_OUT },
        {
          id: "ctl_test_system",
          current_preference: undefined,
        },
      ]);

      // The rest should be undefined
      const keys: Array<keyof TcfExperienceRecords> = [
        "tcf_purpose_legitimate_interests",
        "tcf_special_purposes",
        "tcf_features",
        "tcf_special_features",
        "tcf_vendor_consents",
        "tcf_vendor_legitimate_interests",
        "tcf_purpose_consents",
        "tcf_system_legitimate_interests",
      ];
      keys.forEach((key) => {
        updatedExperience[key]?.forEach((f) => {
          expect(f.current_preference).toEqual(undefined);
        });
      });
    });
  });
});
