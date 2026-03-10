import {
  ConsentMechanism,
  NoticeConsent,
  PrivacyNotice,
  SaveConsentPreference,
  UserConsentPreference,
} from "../../src/lib/consent-types";
import {
  buildConsentPreferencesArray,
  noticeHasConsentInCookie,
  transformConsentToFidesUserPreference,
  transformUserPreferenceToBoolean,
} from "../../src/lib/shared-consent-utils";

describe("shared-consent-utils", () => {
  describe("transformUserPreferenceToBoolean", () => {
    it("should convert OPT_OUT to false", () => {
      expect(
        transformUserPreferenceToBoolean(UserConsentPreference.OPT_OUT),
      ).toBe(false);
    });

    it("should convert OPT_IN to true", () => {
      expect(
        transformUserPreferenceToBoolean(UserConsentPreference.OPT_IN),
      ).toBe(true);
    });

    it("should convert ACKNOWLEDGE to true", () => {
      expect(
        transformUserPreferenceToBoolean(UserConsentPreference.ACKNOWLEDGE),
      ).toBe(true);
    });

    it("should convert undefined to false", () => {
      expect(transformUserPreferenceToBoolean(undefined)).toBe(false);
    });
  });

  describe("transformConsentToFidesUserPreference", () => {
    it("should convert true to OPT_IN for opt-in/opt-out mechanisms", () => {
      expect(
        transformConsentToFidesUserPreference(true, ConsentMechanism.OPT_IN),
      ).toBe(UserConsentPreference.OPT_IN);
      expect(
        transformConsentToFidesUserPreference(true, ConsentMechanism.OPT_OUT),
      ).toBe(UserConsentPreference.OPT_IN);
    });

    it("should convert true to ACKNOWLEDGE for notice-only mechanisms", () => {
      expect(
        transformConsentToFidesUserPreference(
          true,
          ConsentMechanism.NOTICE_ONLY,
        ),
      ).toBe(UserConsentPreference.ACKNOWLEDGE);
    });

    it("should convert false to OPT_OUT regardless of mechanism", () => {
      expect(
        transformConsentToFidesUserPreference(false, ConsentMechanism.OPT_IN),
      ).toBe(UserConsentPreference.OPT_OUT);
      expect(
        transformConsentToFidesUserPreference(false, ConsentMechanism.OPT_OUT),
      ).toBe(UserConsentPreference.OPT_OUT);
      expect(
        transformConsentToFidesUserPreference(
          false,
          ConsentMechanism.NOTICE_ONLY,
        ),
      ).toBe(UserConsentPreference.OPT_OUT);
    });
  });

  describe("noticeHasConsentInCookie", () => {
    it("should return true when notice key exists in consent", () => {
      const notice = {
        notice_key: "analytics",
      } as any;
      const consent: NoticeConsent = {
        analytics: true,
      };
      expect(noticeHasConsentInCookie(notice, consent)).toBe(true);
    });

    it("should return false when notice key does not exist in consent", () => {
      const notice = {
        notice_key: "marketing",
      } as any;
      const consent: NoticeConsent = {
        analytics: true,
      };
      expect(noticeHasConsentInCookie(notice, consent)).toBe(false);
    });
  });

  describe("buildConsentPreferencesArray", () => {
    const mockNotices: PrivacyNotice[] = [
      {
        id: "notice-1",
        notice_key: "analytics",
        name: "Analytics",
        consent_mechanism: ConsentMechanism.OPT_OUT,
        has_gpc_flag: true,
        default_preference: UserConsentPreference.OPT_OUT,
        translations: [
          {
            language: "en",
            title: "Analytics",
            description: "Analytics description",
            privacy_notice_history_id: "history-1",
          },
          {
            language: "es",
            title: "Analítica",
            description: "Descripción de analítica",
            privacy_notice_history_id: "history-1-es",
          },
        ],
      } as PrivacyNotice,
      {
        id: "notice-2",
        notice_key: "marketing",
        name: "Marketing",
        consent_mechanism: ConsentMechanism.OPT_IN,
        has_gpc_flag: false,
        default_preference: UserConsentPreference.OPT_OUT,
        translations: [
          {
            language: "en",
            title: "Marketing",
            description: "Marketing description",
            privacy_notice_history_id: "history-2",
          },
        ],
      } as PrivacyNotice,
      {
        id: "notice-3",
        notice_key: "essential",
        name: "Essential",
        consent_mechanism: ConsentMechanism.NOTICE_ONLY,
        has_gpc_flag: false,
        default_preference: UserConsentPreference.ACKNOWLEDGE,
        translations: [
          {
            language: "en",
            title: "Essential",
            description: "Essential description",
            privacy_notice_history_id: "history-3",
          },
        ],
      } as PrivacyNotice,
    ];

    describe("with fullObjects = true (default)", () => {
      it("should build full SaveConsentPreference objects from boolean consent values", () => {
        const noticeConsent: NoticeConsent = {
          analytics: false,
          marketing: true,
        };

        const result = buildConsentPreferencesArray(
          noticeConsent,
          mockNotices,
          "en",
          "en",
          true,
        );

        expect(result).toHaveLength(2);
        expect(result[0]).toBeInstanceOf(SaveConsentPreference);
        expect(result[0].notice).toEqual(mockNotices[0]);
        expect(result[0].consentPreference).toBe(UserConsentPreference.OPT_OUT);
        expect(result[0].noticeHistoryId).toBe("history-1");

        expect(result[1]).toBeInstanceOf(SaveConsentPreference);
        expect(result[1].notice).toEqual(mockNotices[1]);
        expect(result[1].consentPreference).toBe(UserConsentPreference.OPT_IN);
        expect(result[1].noticeHistoryId).toBe("history-2");
      });

      it("should build full SaveConsentPreference objects from UserConsentPreference values", () => {
        const noticeConsent: NoticeConsent = {
          analytics: UserConsentPreference.OPT_OUT,
          marketing: UserConsentPreference.OPT_IN,
        };

        const result = buildConsentPreferencesArray(
          noticeConsent,
          mockNotices,
          "en",
          "en",
          true,
        );

        expect(result).toHaveLength(2);
        expect(result[0].consentPreference).toBe(UserConsentPreference.OPT_OUT);
        expect(result[1].consentPreference).toBe(UserConsentPreference.OPT_IN);
      });

      it("should handle NOTICE_ONLY mechanisms correctly", () => {
        const noticeConsent: NoticeConsent = {
          essential: true,
        };

        const result = buildConsentPreferencesArray(
          noticeConsent,
          mockNotices,
          "en",
          "en",
          true,
        );

        expect(result).toHaveLength(1);
        expect(result[0].consentPreference).toBe(
          UserConsentPreference.ACKNOWLEDGE,
        );
      });

      it("should use the best translation based on locale", () => {
        const noticeConsent: NoticeConsent = {
          analytics: false,
        };

        const result = buildConsentPreferencesArray(
          noticeConsent,
          mockNotices,
          "es",
          "en",
        );

        expect(result).toHaveLength(1);
        expect(result[0].noticeHistoryId).toBe("history-1-es");
      });

      it("should fall back to default locale when preferred locale not available", () => {
        const noticeConsent: NoticeConsent = {
          marketing: true,
        };

        const result = buildConsentPreferencesArray(
          noticeConsent,
          mockNotices,
          "fr",
          "en",
        );

        expect(result).toHaveLength(1);
        expect(result[0].noticeHistoryId).toBe("history-2");
      });

      it("should skip notices without history IDs", () => {
        const noticesWithoutHistory: PrivacyNotice[] = [
          {
            id: "notice-no-history",
            notice_key: "no_history",
            name: "No History",
            consent_mechanism: ConsentMechanism.OPT_OUT,
            translations: [
              {
                language: "en",
                title: "No History",
                description: "No history description",
                // Missing privacy_notice_history_id
              },
            ],
          } as PrivacyNotice,
        ];

        const noticeConsent: NoticeConsent = {
          no_history: false,
        };

        const result = buildConsentPreferencesArray(
          noticeConsent,
          noticesWithoutHistory,
          "en",
          "en",
        );

        expect(result).toHaveLength(0);
      });

      it("should skip notices not in the consent object", () => {
        const noticeConsent: NoticeConsent = {
          analytics: false,
          // marketing is not included
        };

        const result = buildConsentPreferencesArray(
          noticeConsent,
          mockNotices,
          "en",
          "en",
        );

        expect(result).toHaveLength(1);
        expect(result[0].notice.notice_key).toBe("analytics");
      });

      it("should return empty array when no notices match", () => {
        const noticeConsent: NoticeConsent = {
          nonexistent: true,
        };

        const result = buildConsentPreferencesArray(
          noticeConsent,
          mockNotices,
          "en",
          "en",
        );

        expect(result).toHaveLength(0);
      });
    });

    describe("with fullObjects = false", () => {
      it("should build minimal objects with just noticeHistoryId and consentPreference", () => {
        const noticeConsent: NoticeConsent = {
          analytics: false,
          marketing: true,
        };

        const result = buildConsentPreferencesArray(
          noticeConsent,
          mockNotices,
          "en",
          "en",
          false,
        );

        expect(result).toHaveLength(2);
        expect(result[0]).toEqual({
          noticeHistoryId: "history-1",
          consentPreference: UserConsentPreference.OPT_OUT,
        });
        expect(result[1]).toEqual({
          noticeHistoryId: "history-2",
          consentPreference: UserConsentPreference.OPT_IN,
        });
        // Should not be instances of SaveConsentPreference
        expect(result[0]).not.toBeInstanceOf(SaveConsentPreference);
      });

      it("should handle mixed boolean and UserConsentPreference values", () => {
        const noticeConsent: NoticeConsent = {
          analytics: false,
          marketing: UserConsentPreference.OPT_IN,
          essential: UserConsentPreference.ACKNOWLEDGE,
        };

        const result = buildConsentPreferencesArray(
          noticeConsent,
          mockNotices,
          "en",
          "en",
          false,
        );

        expect(result).toHaveLength(3);
        expect(result[0].consentPreference).toBe(UserConsentPreference.OPT_OUT);
        expect(result[1].consentPreference).toBe(UserConsentPreference.OPT_IN);
        expect(result[2].consentPreference).toBe(
          UserConsentPreference.ACKNOWLEDGE,
        );
      });
    });

    describe("edge cases", () => {
      it("should handle empty notices array", () => {
        const noticeConsent: NoticeConsent = {
          analytics: true,
        };

        const result = buildConsentPreferencesArray(
          noticeConsent,
          [],
          "en",
          "en",
        );

        expect(result).toHaveLength(0);
      });

      it("should handle empty consent object", () => {
        const result = buildConsentPreferencesArray(
          {},
          mockNotices,
          "en",
          "en",
        );

        expect(result).toHaveLength(0);
      });

      it("should handle undefined consent values by skipping them", () => {
        const noticeConsent: NoticeConsent = {
          analytics: undefined as any,
          marketing: true,
        };

        const result = buildConsentPreferencesArray(
          noticeConsent,
          mockNotices,
          "en",
          "en",
        );

        // Should only include marketing, not analytics
        expect(result).toHaveLength(1);
        expect(result[0].notice.notice_key).toBe("marketing");
      });
    });
  });
});
