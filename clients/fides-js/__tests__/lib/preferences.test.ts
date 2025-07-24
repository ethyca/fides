/* eslint-disable global-require */
import {
  ConsentMechanism,
  ConsentMethod,
  UpdateConsentValidation,
  UserConsentPreference,
} from "../../src/lib/consent-types";
import { decodeNoticeConsentString } from "../../src/lib/consent-utils";
import { decodeFidesString } from "../../src/lib/fides-string";
import {
  updateConsent,
  updateConsentPreferences,
} from "../../src/lib/preferences";
import { createMockFides } from "../__utils__/test-utils";

// Mock dependencies
jest.mock("../../src/lib/fides-string");
jest.mock("../../src/lib/consent-utils");

describe("preferences", () => {
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
    // Reset the mock implementations
    updatePreferencesSpy.mockClear();
    updatePreferencesSpy.mockResolvedValue(undefined);
  });

  describe("updateConsent", () => {
    beforeEach(() => {
      jest.clearAllMocks();

      // Mock decodeFidesString to return a valid value
      (decodeFidesString as jest.Mock).mockReturnValue({
        nc: "encoded-consent",
      });

      // We need to explicitly mock updateConsentPreferences so it doesn't actually run
      // which would cause our validation tests to fail when they should pass
      updatePreferencesSpy.mockResolvedValue(undefined);
    });

    it("should reject when experience is not initialized", async () => {
      const mockFides = createMockFides({ experience: undefined });
      await expect(
        updateConsent(mockFides, {
          noticeConsent: { analytics: true },
          consentMethod: ConsentMethod.SCRIPT,
        }),
      ).rejects.toThrow(
        "Experience must be initialized before updating consent",
      );
    });

    it("should reject when cookie is not initialized", async () => {
      const mockFides = createMockFides({ cookie: undefined });
      await expect(
        updateConsent(mockFides, {
          noticeConsent: { analytics: true },
          consentMethod: ConsentMethod.SCRIPT,
        }),
      ).rejects.toThrow("Cookie is not initialized");
    });

    it("should reject when consent key is in non_applicable_privacy_notices", async () => {
      const mockFides = createMockFides();

      // Setup a notice in non_applicable_privacy_notices
      (mockFides.experience as any).non_applicable_privacy_notices = [
        "marketing",
      ];

      // Try to set a non-applicable notice key to false
      await expect(
        updateConsent(mockFides, {
          noticeConsent: { marketing: false },
          consentMethod: ConsentMethod.SCRIPT,
        }),
      ).rejects.toThrow(/is not applicable/);
    });

    it("should reject when consent key is not a valid notice key", async () => {
      const mockFides = createMockFides();

      // Setup privacy notices but not including the one we'll try to use
      (mockFides.experience as any).privacy_notices = [
        {
          notice_key: "analytics",
          id: "analytics-id",
          consent_mechanism: ConsentMechanism.OPT_IN,
          cookies: [],
          translations: [
            { language: "en", privacy_notice_history_id: "history-analytics" },
          ],
        },
      ];

      // Empty the non_applicable_privacy_notices to ensure our test key isn't there
      (mockFides.experience as any).non_applicable_privacy_notices = [];

      // Try to use a key that doesn't exist in either privacy_notices or non_applicable_privacy_notices
      await expect(
        updateConsent(mockFides, {
          noticeConsent: { nonexistent: true },
          consentMethod: ConsentMethod.SCRIPT,
        }),
      ).rejects.toThrow(/not a valid notice key/);
    });

    it("should update consent from a provided consent object", async () => {
      const mockConsent = { analytics: true, marketing: false };
      const mockFides = createMockFides();

      // Setup privacy notices in the experience to match the consent keys
      (mockFides.experience as any).privacy_notices = [
        {
          notice_key: "analytics",
          id: "analytics-id",
          consent_mechanism: ConsentMechanism.OPT_IN,
          cookies: [],
          translations: [
            { language: "en", privacy_notice_history_id: "history-analytics" },
          ],
        },
        {
          notice_key: "marketing",
          id: "marketing-id",
          consent_mechanism: ConsentMechanism.OPT_OUT,
          cookies: [],
          translations: [
            { language: "en", privacy_notice_history_id: "history-marketing" },
          ],
        },
      ] as any[];

      await updateConsent(mockFides, {
        noticeConsent: mockConsent,
        consentMethod: ConsentMethod.SCRIPT,
      });

      // Verify updateConsentPreferences was called with the right args
      expect(updatePreferencesSpy).toHaveBeenCalledTimes(1);
      const callArgs = updatePreferencesSpy.mock.calls[0][0];

      // Check that consentPreferencesToSave contains the right preferences
      expect(callArgs.consentPreferencesToSave).toHaveLength(2);

      // Check the conversion from boolean to preference type (using find for more robust testing)
      const analyticsPref = callArgs.consentPreferencesToSave!.find(
        (pref) => pref.notice.notice_key === "analytics",
      );
      expect(analyticsPref).toBeDefined();
      expect(analyticsPref!.consentPreference).toBe(
        UserConsentPreference.OPT_IN,
      );

      const marketingPref = callArgs.consentPreferencesToSave!.find(
        (pref) => pref.notice.notice_key === "marketing",
      );
      expect(marketingPref).toBeDefined();
      expect(marketingPref!.consentPreference).toBe(
        UserConsentPreference.OPT_OUT,
      );

      // Check other important parameters
      expect(callArgs.consentMethod).toBe(ConsentMethod.SCRIPT);
      expect(callArgs.cookie).toBe(mockFides.cookie);
      expect(callArgs.experience).toBe(mockFides.experience);
    });

    it("should update consent from a provided fidesString", async () => {
      const mockFides = createMockFides();

      // Set up the decoded fidesString result through the mock
      const decodedConsent = { analytics: true };
      const mockDecodeFidesString = jest
        .fn()
        .mockReturnValue({ nc: "encoded-consent" });
      (decodeFidesString as jest.Mock).mockImplementation(
        mockDecodeFidesString,
      );

      (decodeNoticeConsentString as jest.Mock).mockReturnValue(decodedConsent);

      // Setup privacy notices in the experience to match the consent keys
      (mockFides.experience as any).privacy_notices = [
        {
          notice_key: "analytics",
          id: "analytics-id",
          consent_mechanism: ConsentMechanism.OPT_IN,
          cookies: [],
          translations: [
            { language: "en", privacy_notice_history_id: "history-analytics" },
          ],
        },
      ] as any[];

      await updateConsent(mockFides, {
        fidesString: "some-encoded-string",
        consentMethod: ConsentMethod.SCRIPT,
      });

      // Verify decodeFidesString was called
      expect(mockDecodeFidesString).toHaveBeenCalledWith("some-encoded-string");

      // Verify decodeNoticeConsentString was called
      expect(decodeNoticeConsentString).toHaveBeenCalledWith("encoded-consent");

      // Verify updateConsentPreferences was called with the right args
      expect(updatePreferencesSpy).toHaveBeenCalledTimes(1);
      const callArgs = updatePreferencesSpy.mock.calls[0][0];

      // Check that consentPreferencesToSave contains the right preferences
      expect(callArgs.consentPreferencesToSave).toHaveLength(1);

      const [analyticsPref] = callArgs.consentPreferencesToSave!;
      expect(analyticsPref.notice.notice_key).toBe("analytics");
      expect(analyticsPref.consentPreference).toBe(
        UserConsentPreference.OPT_IN,
      );
    });

    it("should handle string consent values (opt_in/opt_out)", async () => {
      const mockFides = createMockFides();

      // Setup privacy notices for different consent mechanisms
      (mockFides.experience as any).privacy_notices = [
        {
          notice_key: "analytics",
          id: "analytics-id",
          consent_mechanism: ConsentMechanism.OPT_IN,
          cookies: [],
          translations: [
            { language: "en", privacy_notice_history_id: "history-analytics" },
          ],
        },
        {
          notice_key: "marketing",
          id: "marketing-id",
          consent_mechanism: ConsentMechanism.OPT_OUT,
          cookies: [],
          translations: [
            { language: "en", privacy_notice_history_id: "history-marketing" },
          ],
        },
      ];

      // Use string values for consent
      await updateConsent(mockFides, {
        noticeConsent: {
          analytics: UserConsentPreference.OPT_IN,
          marketing: UserConsentPreference.OPT_OUT,
        },
        consentMethod: ConsentMethod.SCRIPT,
      });

      // Verify updateConsentPreferences was called with the right args
      expect(updatePreferencesSpy).toHaveBeenCalledTimes(1);
      const callArgs = updatePreferencesSpy.mock.calls[0][0];

      // Check that consentPreferencesToSave contains the right preferences
      expect(callArgs.consentPreferencesToSave).toHaveLength(2);

      // String values should be passed through directly
      const analyticsPref = callArgs.consentPreferencesToSave!.find(
        (pref) => pref.notice.notice_key === "analytics",
      );
      expect(analyticsPref).toBeDefined();
      expect(analyticsPref!.consentPreference).toBe(
        UserConsentPreference.OPT_IN,
      );

      const marketingPref = callArgs.consentPreferencesToSave!.find(
        (pref) => pref.notice.notice_key === "marketing",
      );
      expect(marketingPref).toBeDefined();
      expect(marketingPref!.consentPreference).toBe(
        UserConsentPreference.OPT_OUT,
      );
    });

    it("should handle mixed consent value types (boolean and string)", async () => {
      const mockFides = createMockFides();

      // Setup privacy notices for different consent mechanisms
      (mockFides.experience as any).privacy_notices = [
        {
          notice_key: "analytics",
          id: "analytics-id",
          consent_mechanism: ConsentMechanism.OPT_IN,
          cookies: [],
          translations: [
            { language: "en", privacy_notice_history_id: "history-analytics" },
          ],
        },
        {
          notice_key: "marketing",
          id: "marketing-id",
          consent_mechanism: ConsentMechanism.OPT_OUT,
          cookies: [],
          translations: [
            { language: "en", privacy_notice_history_id: "history-marketing" },
          ],
        },
      ];

      // Use mixed boolean and string values for consent
      await updateConsent(mockFides, {
        noticeConsent: {
          analytics: true, // boolean
          marketing: UserConsentPreference.OPT_OUT, // string
        },
        consentMethod: ConsentMethod.SCRIPT,
      });

      // Verify updateConsentPreferences was called with the right args
      expect(updatePreferencesSpy).toHaveBeenCalledTimes(1);
      const callArgs = updatePreferencesSpy.mock.calls[0][0];

      // Check that consentPreferencesToSave contains the right preferences
      expect(callArgs.consentPreferencesToSave).toHaveLength(2);

      // Boolean values should be converted, string values should be passed through
      const analyticsPref = callArgs.consentPreferencesToSave!.find(
        (pref) => pref.notice.notice_key === "analytics",
      );
      expect(analyticsPref).toBeDefined();
      expect(analyticsPref!.consentPreference).toBe(
        UserConsentPreference.OPT_IN,
      );

      const marketingPref = callArgs.consentPreferencesToSave!.find(
        (pref) => pref.notice.notice_key === "marketing",
      );
      expect(marketingPref).toBeDefined();
      expect(marketingPref!.consentPreference).toBe(
        UserConsentPreference.OPT_OUT,
      );
    });

    it("should validate consent values based on consent_mechanism", async () => {
      const mockFides = createMockFides();

      // Set up a NOTICE_ONLY mechanism
      (mockFides.experience as any).privacy_notices = [
        {
          notice_key: "essential",
          id: "essential-id",
          consent_mechanism: ConsentMechanism.NOTICE_ONLY,
          cookies: [],
          translations: [
            { language: "en", privacy_notice_history_id: "history-essential" },
          ],
        },
      ];

      // Try to use opt_in for a NOTICE_ONLY type with validation='throw'
      await expect(
        updateConsent(mockFides, {
          noticeConsent: { essential: UserConsentPreference.OPT_IN },
          validation: UpdateConsentValidation.THROW,
          consentMethod: ConsentMethod.SCRIPT,
        }),
      ).rejects.toThrow(/Invalid consent value/);

      // Expect notice-only true to be converted to ACKNOWLEDGE
      await updateConsent(mockFides, {
        noticeConsent: { essential: true },
        validation: UpdateConsentValidation.THROW,
        consentMethod: ConsentMethod.SCRIPT,
      });
      expect(updatePreferencesSpy).toHaveBeenCalledTimes(1);
      const callArgs = updatePreferencesSpy.mock.calls[0][0];
      expect(callArgs.consentPreferencesToSave).toHaveLength(1);
      expect(callArgs.consentPreferencesToSave![0].consentPreference).toBe(
        UserConsentPreference.ACKNOWLEDGE,
      );
    });

    it("should handle NOTICE_ONLY consent mechanisms", async () => {
      const mockFides = createMockFides();

      // Setup privacy notice with NOTICE_ONLY mechanism
      (mockFides.experience as any).privacy_notices = [
        {
          notice_key: "essential",
          id: "essential-id",
          consent_mechanism: ConsentMechanism.NOTICE_ONLY,
          cookies: [],
          translations: [
            { language: "en", privacy_notice_history_id: "history-essential" },
          ],
        },
      ];

      // Test with explicit ACKNOWLEDGE value
      await updateConsent(mockFides, {
        noticeConsent: {
          essential: UserConsentPreference.ACKNOWLEDGE,
        },
        consentMethod: ConsentMethod.SCRIPT,
      });

      // Verify updateConsentPreferences was called with the right args
      expect(updatePreferencesSpy).toHaveBeenCalledTimes(1);
      let callArgs = updatePreferencesSpy.mock.calls[0][0];
      let [essentialPref] = callArgs.consentPreferencesToSave!;

      expect(essentialPref.notice.notice_key).toBe("essential");
      expect(essentialPref.consentPreference).toBe(
        UserConsentPreference.ACKNOWLEDGE,
      );

      // Reset mock for next test
      updatePreferencesSpy.mockClear();

      // Test that NOTICE_ONLY forces ACKNOWLEDGE when using validation="ignore"
      await updateConsent(mockFides, {
        noticeConsent: {
          // This would be invalid with validation="throw", but we're using "ignore"
          essential: true,
        },
        validation: UpdateConsentValidation.IGNORE,
        consentMethod: ConsentMethod.SCRIPT,
      });

      // Verify updateConsentPreferences was called with the right args
      expect(updatePreferencesSpy).toHaveBeenCalledTimes(1);
      // eslint-disable-next-line prefer-destructuring
      callArgs = updatePreferencesSpy.mock.calls[0][0];
      [essentialPref] = callArgs.consentPreferencesToSave!;

      expect(essentialPref.notice.notice_key).toBe("essential");
      // Even though we passed 'true', it should be converted to ACKNOWLEDGE
      expect(essentialPref.consentPreference).toBe(
        UserConsentPreference.ACKNOWLEDGE,
      );
    });
  });
});
