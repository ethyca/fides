/* eslint-disable global-require */
import {
  FidesCookie,
  FidesGlobal,
  NoticeValues,
  PrivacyExperience,
  UserConsentPreference,
} from "../../src/lib/consent-types";
import { decodeFidesString } from "../../src/lib/fides-string";
import {
  updateConsent,
  updateConsentPreferences,
} from "../../src/lib/preferences";
import mockExperienceJSON from "../__fixtures__/mock_experience.json";

// Mock dependencies
jest.mock("../../src/lib/fides-string");
jest.mock("../../src/lib/consent-utils");

// Setup mocks
const mockDecodeFidesString = decodeFidesString as jest.MockedFunction<
  typeof decodeFidesString
>;

describe("preferences", () => {
  const mockExperience: Partial<PrivacyExperience> = mockExperienceJSON as any;
  const updatePreferencesSpy = jest
    .spyOn(require("../../src/lib/preferences"), "updateConsentPreferences")
    .mockResolvedValue(undefined) as jest.MockedFunction<
    typeof updateConsentPreferences
  >;
  beforeAll(() => {
    window.fidesDebugger = jest.fn();
  });

  beforeEach(() => {
    jest.resetAllMocks();
  });

  describe("updateConsent", () => {
    // Create a mock Fides object that we can reuse in tests
    const createMockFides = (overrides = {}): FidesGlobal => {
      const mockCookie: FidesCookie = {
        consent: {},
        identity: {},
        fides_meta: {},
        tcf_consent: {},
      };

      return {
        consent: {},
        experience: mockExperience,
        geolocation: { country: "US" },
        locale: "en",
        options: {
          debug: true,
          fidesApiUrl: "https://example.com/api",
          fidesDisableSaveApi: false,
        },
        fides_meta: {},
        identity: {},
        tcf_consent: {},
        saved_consent: {},
        config: { propertyId: "prop1" },
        initialized: true,
        cookie: mockCookie,
        encodeNoticeConsentString: jest.fn().mockReturnValue("encoded-string"),
        decodeNoticeConsentString: jest
          .fn()
          .mockReturnValue({ analytics: true }),
        ...overrides,
      } as unknown as FidesGlobal;
    };

    // Test: Successfully updating consent with a consent object
    it("should update consent with a consent object", async () => {
      // ARRANGE
      const mockFides = createMockFides();
      mockFides.experience!.privacy_notices = [
        {
          id: "notice1",
          notice_key: "analytics",
          translations: [
            {
              language: "en",
              privacy_notice_history_id: "history-analytics",
            },
          ],
          cookies: [],
          created_at: "",
          updated_at: "",
        },
        {
          id: "notice2",
          notice_key: "marketing",
          translations: [
            {
              language: "en",
              privacy_notice_history_id: "history-marketing",
            },
          ],
          cookies: [],
          created_at: "",
          updated_at: "",
        },
      ];
      const consentValues: NoticeValues = {
        analytics: true,
        marketing: false,
      };

      // ACT
      await updateConsent(mockFides, { consent: consentValues });

      // ASSERT
      expect(updatePreferencesSpy).toHaveBeenCalledTimes(1);

      // Verify cookie consent was updated
      const updateCookieFn = updatePreferencesSpy.mock.calls[0][0].updateCookie;
      const updatedCookie = await updateCookieFn({} as FidesCookie);
      expect(updatedCookie.consent).toEqual(consentValues);

      // Verify consentPreferencesToSave contains correct preferences
      const savedPreferences =
        updatePreferencesSpy.mock.calls[0][0].consentPreferencesToSave;
      expect(savedPreferences).toHaveLength(2);
      expect(savedPreferences![0].consentPreference).toBe(
        UserConsentPreference.OPT_IN,
      );
      expect(savedPreferences![1].consentPreference).toBe(
        UserConsentPreference.OPT_OUT,
      );
    });

    // Test: Successfully updating consent with a fidesString
    it("should update consent with a fidesString", async () => {
      // ARRANGE
      const mockFides = createMockFides();
      const fidesString = "tc.encoded-nc-string.gpp";

      mockDecodeFidesString.mockReturnValue({
        tc: "tc",
        ac: "",
        gpp: "gpp",
        nc: "encoded-nc-string",
      });

      // ACT
      await updateConsent(mockFides, { fidesString });

      // ASSERT
      expect(mockDecodeFidesString).toHaveBeenCalledWith(fidesString);
      expect(mockFides.decodeNoticeConsentString).toHaveBeenCalledWith(
        "encoded-nc-string",
      );
      expect(updatePreferencesSpy).toHaveBeenCalledTimes(1);

      // Verify cookie fides_string was updated
      const updateCookieFn = updatePreferencesSpy.mock.calls[0][0].updateCookie;
      const updatedCookie = await updateCookieFn({} as FidesCookie);
      expect(updatedCookie.fides_string).toBe(fidesString);
    });

    // Test: fidesString should take priority over consent object
    it("should prioritize fidesString over consent object", async () => {
      // ARRANGE
      const mockFides = createMockFides();
      const consentValues: NoticeValues = {
        analytics: false,
        marketing: true,
      };
      const fidesString = "tc.encoded-nc-string.gpp";

      mockDecodeFidesString.mockReturnValue({
        tc: "tc",
        ac: "",
        gpp: "gpp",
        nc: "encoded-nc-string",
      });

      const decodedConsent = {
        analytics: true,
        marketing: false,
      };

      mockFides.decodeNoticeConsentString = jest
        .fn()
        .mockReturnValue(decodedConsent);

      // ACT
      await updateConsent(mockFides, { consent: consentValues, fidesString });

      // ASSERT
      expect(updatePreferencesSpy).toHaveBeenCalledTimes(1);

      // Verify the decoded string values are used, not the consent object
      const updateCookieFn = updatePreferencesSpy.mock.calls[0][0].updateCookie;
      const updatedCookie = await updateCookieFn({} as FidesCookie);
      expect(updatedCookie.consent).toEqual(decodedConsent);
    });

    // Test: Error if neither consent nor fidesString are provided
    it("should reject if neither consent nor fidesString are provided", async () => {
      // ARRANGE
      const mockFides = createMockFides();

      // ACT & ASSERT
      await expect(updateConsent(mockFides, {})).rejects.toThrow(
        "Either consent or fidesString must be provided",
      );
    });

    // Test: Error if fidesString is invalid
    it("should reject if fidesString is invalid", async () => {
      // ARRANGE
      const mockFides = createMockFides();
      const fidesString = "invalid-string";

      mockDecodeFidesString.mockImplementation(() => {
        throw new Error("Invalid format");
      });

      // ACT & ASSERT
      await expect(updateConsent(mockFides, { fidesString })).rejects.toThrow(
        "Invalid fidesString provided: Invalid format",
      );
    });

    // Test: Error if cookie is not initialized
    it("should reject if cookie is not initialized", async () => {
      // ARRANGE
      const mockFides = createMockFides({ cookie: undefined });
      const consentValues: NoticeValues = {
        analytics: true,
      };

      // ACT & ASSERT
      await expect(
        updateConsent(mockFides, { consent: consentValues }),
      ).rejects.toThrow("Cookie is not initialized");
    });

    // Test: Error if experience is not available
    it("should reject if experience is not available", async () => {
      // ARRANGE
      const mockFides = createMockFides({ experience: undefined });
      const consentValues: NoticeValues = {
        analytics: true,
      };

      // ACT & ASSERT
      await expect(
        updateConsent(mockFides, { consent: consentValues }),
      ).rejects.toThrow("Cannot update consent without an experience");
    });

    // Test: Warning when notice key doesn't exist in experience
    it("should log a warning when notice key does not exist in experience", async () => {
      // ARRANGE
      const mockFides = createMockFides();
      const consentValues: NoticeValues = {
        analytics: true,
        nonexistent: false,
      };

      // ACT
      await updateConsent(mockFides, { consent: consentValues });

      // ASSERT
      expect(window.fidesDebugger).toHaveBeenCalledWith(
        'Warning: Notice key "nonexistent" does not exist in the current experience',
      );

      // Only analytics should be saved, not nonexistent
      const savedPreferences =
        updatePreferencesSpy.mock.calls[0][0].consentPreferencesToSave;
      expect(savedPreferences).toHaveLength(1);
      expect(savedPreferences![0].notice.notice_key).toBe("analytics");
    });

    // Test: Creates fidesString with proper format when none exists
    it("should create proper fidesString format when none exists", async () => {
      // ARRANGE
      const mockFides = createMockFides();
      const consentValues: NoticeValues = {
        analytics: true,
      };

      // ACT
      await updateConsent(mockFides, { consent: consentValues });

      // ASSERT
      const updateCookieFn = updatePreferencesSpy.mock.calls[0][0].updateCookie;
      const updatedCookie = await updateCookieFn({} as FidesCookie);

      // Should have format .nc. (empty tc and gpp sections)
      expect(updatedCookie.fides_string).toBe(".encoded-string.");
    });

    // Test: Preserves existing fidesString parts when updating consent
    it("should preserve existing fidesString parts when updating with consent", async () => {
      // ARRANGE
      const existingFidesString = "existing-tc.existing-nc.existing-gpp";
      const mockFides = createMockFides({
        cookie: {
          consent: {},
          identity: {},
          fides_meta: {},
          tcf_consent: {},
          fides_string: existingFidesString,
        },
      });

      const consentValues: NoticeValues = {
        analytics: true,
      };

      mockDecodeFidesString.mockReturnValue({
        tc: "existing-tc",
        ac: "",
        gpp: "existing-gpp",
        nc: "existing-nc",
      });

      // ACT
      await updateConsent(mockFides, { consent: consentValues });

      // ASSERT
      expect(mockFides.encodeNoticeConsentString).toHaveBeenCalledWith(
        consentValues,
      );

      const updateCookieFn = updatePreferencesSpy.mock.calls[0][0].updateCookie;
      const updatedCookie = await updateCookieFn({} as FidesCookie);

      // Should maintain tc and gpp sections, but update nc section
      expect(updatedCookie.fides_string).toBe(
        "existing-tc.encoded-string.existing-gpp",
      );
    });
  });
});
