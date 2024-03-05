import {
  ExperienceConfig,
  FidesOptions,
  PrivacyExperience,
  PrivacyNoticeWithPreference,
} from "~/fides";
import {
  LOCALE_REGEX,
  detectUserLocale,
  getCurrentLocale,
  initializeI18n,
  loadMessagesFromExperience,
  loadMessagesFromFiles,
  selectBestNoticeTranslation,
  matchAvailableLocales,
  messageExists,
  setupI18n,
} from "~/lib/i18n";
import messagesEn from "~/lib/i18n/locales/en/messages.json";
import messagesEs from "~/lib/i18n/locales/es/messages.json";
import type { I18n, Locale, MessageDescriptor, Messages } from "~/lib/i18n";

import mockExperienceJSON from "../../__fixtures__/mock_experience.json";

describe("i18n-utils", () => {
  // Define a mock implementation of the i18n singleton for tests
  let mockCurrentLocale = "";
  const mockI18n = {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    activate: jest.fn((locale: Locale): void => {
      mockCurrentLocale = locale;
    }),
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    load: jest.fn((locale: Locale, messages: Messages): void => {}),
    t: jest.fn(
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      (idOrDescriptor: string | MessageDescriptor): string => "mock translate"
    ),
    get locale(): Locale {
      return mockCurrentLocale;
    },
  };

  const mockExperience: Partial<PrivacyExperience> = mockExperienceJSON as any;

  afterEach(() => {
    mockI18n.activate.mockClear();
    mockI18n.load.mockClear();
    mockI18n.t.mockClear();
  });

  describe("initializeI18n", () => {
    it("initializes the i18n singleton with messages (from both files and experience API) and activates the best match for user's locale", () => {
      const mockNavigator: Partial<Navigator> = {
        language: "es-419",
      };

      initializeI18n(mockI18n, mockNavigator, mockExperience);
      expect(mockI18n.load).toHaveBeenCalledWith("en", messagesEn);
      expect(mockI18n.load).toHaveBeenCalledWith("es", messagesEs);
      expect(mockI18n.activate).toHaveBeenCalledWith("es");

      // Expect that messages are loaded from both static files & experience API
      const loadCallsEn = mockI18n.load.mock.calls.filter((e) => e[0] === "en");
      expect(loadCallsEn).toHaveLength(2);
      const fileMessagesEn = loadCallsEn[0][1];
      const experienceMessagesEn = loadCallsEn[1][1];
      expect(fileMessagesEn).toEqual(messagesEn);
      expect(experienceMessagesEn).toMatchObject({
        "exp.title": "Title Test",
        "exp.accept_button_label": "Accept Test",
      });
    });

    it("does not automatically detect the user's locale when the experience disables auto-detection", () => {
      // Make a deep copy of the mock experience using a dirty JSON serialization trick
      // NOTE: This is why lodash exists, but I'm not going to install it just for this! :)
      const mockExpNoAutoDetect = JSON.parse(JSON.stringify(mockExperience));
      mockExpNoAutoDetect.experience_config.auto_detect_language = false;

      const mockNavigator: Partial<Navigator> = {
        language: "es-419",
      };

      initializeI18n(mockI18n, mockNavigator, mockExpNoAutoDetect);
      expect(mockI18n.load).toHaveBeenCalledWith("en", messagesEn);
      expect(mockI18n.load).toHaveBeenCalledWith("es", messagesEs);
      expect(mockI18n.activate).toHaveBeenCalledWith("en");
    });
  });

  describe("loadMessagesFromFiles", () => {
    it("reads all static messages from source and loads into the i18n catalog", () => {
      const updatedLocales = loadMessagesFromFiles(mockI18n);

      // Check the updated locales list is what we expect
      const EXPECTED_NUM_STATIC_LOCALES = 3; // NOTE: manually update this as new locales added
      expect(updatedLocales).toEqual(["en", "es", "fr"]);
      expect(mockI18n.load).toHaveBeenCalledTimes(EXPECTED_NUM_STATIC_LOCALES);

      // Verify the first two locales match the expected catalogues, too
      const [firstLocale, firstMessages] = mockI18n.load.mock.calls[0];
      const [secondLocale, secondMessages] = mockI18n.load.mock.calls[1];
      expect(firstLocale).toEqual("en");
      expect(firstMessages).toEqual(messagesEn);
      expect(secondLocale).toEqual("es");
      expect(secondMessages).toEqual(messagesEs);
    });
  });

  describe("loadMessagesFromExperience", () => {
    it("reads all messages from experience API response and loads into the i18n catalog", () => {
      const updatedLocales = loadMessagesFromExperience(
        mockI18n,
        mockExperience
      );
      const EXPECTED_NUM_TRANSLATIONS = 2;
      expect(updatedLocales).toEqual(["en", "es"]);
      expect(mockI18n.load).toHaveBeenCalledTimes(EXPECTED_NUM_TRANSLATIONS);
      const [firstLocale, firstMessages] = mockI18n.load.mock.calls[0];
      expect(firstLocale).toEqual("en");
      expect(firstMessages).toEqual({
        "exp.accept_button_label": "Accept Test",
        "exp.acknowledge_button_label": "Acknowledge Test",
        "exp.banner_description": "Banner Description Test",
        "exp.banner_title": "Banner Title Test",
        "exp.description": "Description Test",
        "exp.privacy_policy_link_label": "Privacy Policy Test",
        "exp.privacy_policy_url": "https://privacy.example.com/",
        "exp.privacy_preferences_link_label": "Manage Preferences Test",
        "exp.reject_button_label": "Reject Test",
        "exp.save_button_label": "Save Test",
        "exp.title": "Title Test",
      });
      const [secondLocale, secondMessages] = mockI18n.load.mock.calls[1];
      expect(secondLocale).toEqual("es");
      expect(secondMessages).toEqual({
        "exp.accept_button_label": "Aceptar Prueba",
        "exp.acknowledge_button_label": "Reconocer Prueba",
        "exp.banner_description": "Descripción del Banner de Prueba",
        "exp.banner_title": "Título del Banner de Prueba",
        "exp.description": "Descripción de la Prueba",
        "exp.privacy_policy_link_label": "Política de Privacidad de Prueba",
        "exp.privacy_policy_url": "https://privacy.example.com/es",
        "exp.privacy_preferences_link_label":
          "Administrar Preferencias de Prueba",
        "exp.reject_button_label": "Rechazar Prueba",
        "exp.save_button_label": "Guardar Prueba",
        "exp.title": "Título de la Prueba",
      });
    });

    it("handles nulls and empty strings in API responses", () => {
      // Make a deep copy of the mock experience using a dirty JSON serialization trick
      // NOTE: This is why lodash exists, but I'm not going to install it just for this! :)
      const mockExpEdited = JSON.parse(JSON.stringify(mockExperience));

      // Test that an empty string is treated as a valid message and is loaded
      mockExpEdited.experience_config.translations[0].save_button_label = "";

      // Test that a null value is treated as an invalid message and is ignored
      mockExpEdited.experience_config.translations[0].banner_title = null;

      // Load the "no translations" version of the experience and run tests
      loadMessagesFromExperience(mockI18n, mockExpEdited as any);
      const [locale, messages] = mockI18n.load.mock.calls[0];
      expect(locale).toEqual("en");
      expect(messages).toHaveProperty(["exp.title"], "Title Test");
      expect(messages).toHaveProperty(["exp.save_button_label"], "");
      expect(messages).not.toHaveProperty(["exp.banner_title"]);
    });

    it("handles missing experience/notice translations by falling back to legacy properties", () => {
      // Make a deep copy of the mock experience using a dirty JSON serialization trick
      // NOTE: This is why lodash exists, but I'm not going to install it just for this! :)
      const mockExpNoTranslations = JSON.parse(JSON.stringify(mockExperience));

      // Edit the experience data to match the legacy format (w/o translations)
      delete mockExpNoTranslations.experience_config.translations;

      // Load the "no translations" version of the experience and run tests
      const updatedLocales = loadMessagesFromExperience(
        mockI18n,
        mockExpNoTranslations as any
      );

      const EXPECTED_NUM_TRANSLATIONS = 1;
      expect(updatedLocales).toEqual(["en"]);
      expect(mockI18n.load).toHaveBeenCalledTimes(EXPECTED_NUM_TRANSLATIONS);
      const [firstLocale, firstMessages] = mockI18n.load.mock.calls[0];
      expect(firstLocale).toEqual("en");
      expect(firstMessages).toEqual({
        "exp.accept_button_label": "Accept Test",
        "exp.acknowledge_button_label": "Acknowledge Test",
        "exp.banner_description": "Banner Description Test",
        "exp.banner_title": "Banner Title Test",
        "exp.description": "Description Test",
        "exp.privacy_policy_link_label": "Privacy Policy Test",
        "exp.privacy_policy_url": "https://privacy.example.com/",
        "exp.privacy_preferences_link_label": "Manage Preferences Test",
        "exp.reject_button_label": "Reject Test",
        "exp.save_button_label": "Save Test",
        "exp.title": "Title Test",
      });
    });
  });

  describe("detectUserLocale", () => {
    const mockNavigator: Partial<Navigator> = {
      language: "es",
    };

    it("returns the browser locale by default", () => {
      expect(detectUserLocale(mockNavigator)).toEqual("es");
    });

    it("returns a default fallback if browser locale is missing", () => {
      expect(detectUserLocale({})).toEqual("en");
      expect(detectUserLocale({ language: "" })).toEqual("en");
      expect(detectUserLocale({ language: undefined })).toEqual("en");
    });

    it("returns the fides_locale override if present in options", () => {
      const mockOptions: Partial<FidesOptions> = {
        fidesLocale: "fr",
      };
      expect(detectUserLocale(mockNavigator, mockOptions)).toEqual("fr");
    });
  });

  describe("matchAvailableLocales", () => {
    it("returns an exact match when able", () => {
      const availableLocales = ["en", "es", "fr-CA"];
      expect(matchAvailableLocales("fr-CA", availableLocales)).toEqual("fr-CA");
      expect(matchAvailableLocales("es", availableLocales)).toEqual("es");
    });

    it("falls back to language when language+region is not available", () => {
      const availableLocales = ["en", "es", "fr"];
      expect(matchAvailableLocales("fr-CA", availableLocales)).toEqual("fr");
      expect(matchAvailableLocales("es-ES", availableLocales)).toEqual("es");
    });

    it("falls back to default language when no match is found", () => {
      const availableLocales = ["en", "es", "fr"];
      expect(matchAvailableLocales("zh", availableLocales)).toEqual("en");
      expect(matchAvailableLocales("foo", availableLocales)).toEqual("en");
    });

    it("performs a case-insensitive lookup", () => {
      expect(matchAvailableLocales("fr-ca", ["es", "fr-CA"])).toEqual("fr-CA");
      expect(matchAvailableLocales("Fr-Ca", ["es", "fr-CA"])).toEqual("fr-CA");
      expect(matchAvailableLocales("fr-CA", ["es", "FR-CA"])).toEqual("FR-CA");
    });

    it("handles both underscore and dash-separated locales", () => {
      expect(matchAvailableLocales("fr-CA", ["es", "fr_CA"])).toEqual("fr_CA");
      expect(matchAvailableLocales("fr_CA", ["es", "fr_CA"])).toEqual("fr_CA");
      expect(matchAvailableLocales("fr_ca", ["es", "fr-CA"])).toEqual("fr-CA");
    });
  });

  describe("selectBestNoticeTranslation", () => {
    let mockNotice: PrivacyNoticeWithPreference;

    beforeEach(() => {
      // Assert our test data is valid, so that Typescript is happy!
      if (!mockExperience.privacy_notices) {
        throw new Error("Invalid mock experience test data!");
      }
      [mockNotice] = mockExperience.privacy_notices;
    });

    it("selects an exact match for current locale if available", () => {
      mockCurrentLocale = "es";
      const bestTranslation = selectBestNoticeTranslation(mockI18n, mockNotice);
      expect(bestTranslation).toBeDefined();
      expect(bestTranslation?.language).toEqual("es");
    });

    it("falls back to the default locale if an exact match isn't available", () => {
      mockCurrentLocale = "zh";
      const bestTranslation = selectBestNoticeTranslation(mockI18n, mockNotice);
      expect(bestTranslation).toBeDefined();
      expect(bestTranslation?.language).toEqual("en");
    });

    it("falls back to the first locale if neither exact match nor default locale are available", () => {
      mockCurrentLocale = "zh";
      const mockNoticeNoEnglish: PrivacyNoticeWithPreference = JSON.parse(
        JSON.stringify(mockExperience)
      );
      mockNoticeNoEnglish.translations = [mockNotice.translations[1]];
      expect(mockNoticeNoEnglish.translations.map((e) => e.language)).toEqual([
        "es",
      ]);
      const bestTranslation = selectBestNoticeTranslation(
        mockI18n,
        mockNoticeNoEnglish
      );
      expect(bestTranslation).toBeDefined();
      expect(bestTranslation?.language).toEqual("es");
    });

    it("returns null for invalid/missing translations", () => {
      expect(selectBestNoticeTranslation(mockI18n, null as any)).toBeNull();
      expect(
        selectBestNoticeTranslation(mockI18n, { translations: [] } as any)
      ).toBeNull();
      expect(
        selectBestNoticeTranslation(mockI18n, { translations: null } as any)
      ).toBeNull();
      expect(
        selectBestNoticeTranslation(mockI18n, {
          translations: undefined,
        } as any)
      ).toBeNull();
    });
  });

  describe("LOCALE_REGEX", () => {
    it("validates simple locale strings correctly", () => {
      /**
       * Define a key/value map of test cases where:
       * key = input locale string (e.g. "en-GB")
       * value = expected array results of String.match() (e.g. ["en-GB", "en", "GB"])
       */
      const tests: Record<string, (string | undefined)[] | null> = {
        // Language only
        es: ["es", "es", undefined],
        // Language + region
        "en-GB": ["en-GB", "en", "GB"],
        en_GB: ["en_GB", "en", "GB"],
        "zh-CN": ["zh-CN", "zh", "CN"],
        // 3-letter languages or regions
        yue: ["yue", "yue", undefined],
        "es-419": ["es-419", "es", "419"],
        // Language + script
        "zh-Hans": ["zh-Hans", "zh", "Hans"],
        "az-Cyrl": ["az-Cyrl", "az", "Cyrl"],
        // Language + script + region
        "zh-Hans-HK": ["zh-Hans-HK", "zh", undefined],
        "en-US-POSIX": ["en-US-POSIX", "en", undefined],
        // Not real, but should still be parsed
        "en-FAKE": ["en-FAKE", "en", "FAKE"],
        en_FAKE: ["en_FAKE", "en", "FAKE"],
        // Invalid
        "not a real locale": null,
        "four-INVALID": null,
        "123-english": null,
      };

      Object.keys(tests).forEach((locale) => {
        const expectedResults = tests[locale];
        const match = locale.match(LOCALE_REGEX);
        if (match) {
          // eslint-disable-next-line jest/no-conditional-expect
          expect(Array.from(match)).toEqual(expectedResults);
        } else {
          // eslint-disable-next-line jest/no-conditional-expect
          expect(match).toEqual(expectedResults);
        }
      });
    });
  });

  describe("messageExists", () => {
    it("returns false for empty, null, or invalid messages in the current locale", () => {
      // NOTE: use a "real" i18n instance here to test the library itself
      const testI18n: I18n = setupI18n();
      testI18n.load("es", {
        "test.greeting": "Hola",
        "test.empty": "",
        "test.null": null,
      } as any);
      testI18n.activate("es");
      expect(messageExists(testI18n, "test.greeting")).toBeTruthy();
      expect(messageExists(testI18n, "test.empty")).toBeFalsy();
      expect(messageExists(testI18n, "test.null")).toBeFalsy();
      expect(messageExists(testI18n, "test.missing")).toBeFalsy();
      expect(messageExists(testI18n, { invalid: 1 } as any)).toBeFalsy();
      expect(messageExists(testI18n, "")).toBeFalsy();
    });
  });

  describe("getCurrentLocale", () => {
    it("returns the currently active locale", () => {
      // NOTE: use a "real" i18n instance here to test the library itself
      const testI18n: I18n = setupI18n();
      testI18n.load("es", { "test.greeting": "Hola" });
      expect(getCurrentLocale(testI18n)).toEqual("en");
      testI18n.activate("es");
      expect(getCurrentLocale(testI18n)).toEqual("es");
    });
  });

  describe("__fixtures__ mock data", () => {
    /**
     * Utility type to enforce some type-safety on our mock API fixtures.
     *
     * NOTE: This type looks complicated, but it essentially just surgically
     * replaces enum types (e.g. ConsentMechanism) with basic strings instead. This
     * is because our test data is in JSON format so it won't natively be converted
     * to Typescript enums!
     *
     * In other words, this makes strings like this valid:
     * ```
     * component: "banner_and_modal"
     * ```
     *
     * ...where our regular type would expect this as an enum:
     * ```
     * component: ComponentType.BANNER_AND_MODAL
     * ```
     */
    type MockPrivacyExperience = Omit<
      PrivacyExperience,
      "component" | "experience_config" | "privacy_notices"
    > & {
      component: string;
      experience_config: Omit<ExperienceConfig, "component"> & {
        component: string;
      };
      privacy_notices: Array<
        Omit<
          PrivacyNoticeWithPreference,
          | "consent_mechanism"
          | "enforcement_level"
          | "framework"
          | "default_preference"
          | "cookies"
        > & {
          consent_mechanism: string;
          enforcement_level: string;
          framework: string | null;
          default_preference: string;
          cookies: Array<any>;
        }
      >;
    };

    it("ensures that our test fixtures match our expected types", () => {
      // Assign our JSON import object to the MockPrivacyExperience type to
      // check that the test data matches the latest API
      const mockExpTyped: MockPrivacyExperience = mockExperienceJSON;

      // This test is 99% just for the build-time check above, but throw an
      // assertion in there to keep Jest happy!
      expect(mockExpTyped.experience_config.component).toEqual(
        "banner_and_modal"
      );
    });
  });
});

// Additional tests for the i18n module itself, to guarantee how we expect it to behave
describe("i18n module", () => {
  describe("module exports", () => {
    it("exports a valid i18n object", () => {
      // NOTE: using require() here to avoid importing i18n and accidentally using it!
      // eslint-disable-next-line global-require
      const { i18n } = require("../../../src/lib/i18n");
      expect(i18n).toHaveProperty("activate");
      expect(i18n).toHaveProperty("load");
      expect(i18n).toHaveProperty("t");
    });

    it("exports a setupI18n function to create new i18n instances", () => {
      const testI18n: I18n = setupI18n();
      testI18n.load("fr", { "test.greeting": "Bonjour, Jest!" });
      testI18n.activate("fr");
      expect(testI18n.t({ id: "test.greeting" })).toEqual("Bonjour, Jest!");
    });
  });

  describe("when loading a test messages catalog", () => {
    const testMessagesEn: Messages = {
      "test.greeting": "Hello, Jest!",
      "test.phrase": "Move purposefully and fix things",
      "test.empty": "",
    };

    const testMessagesFr: Messages = {
      "test.greeting": "Bonjour, Jest!",
      "test.phrase": "Déplacez-vous délibérément et réparez les choses",
      "test.empty": "",
    };

    let testI18n: I18n;

    beforeEach(() => {
      testI18n = setupI18n();
      testI18n.load("en", testMessagesEn);
      testI18n.load("fr", testMessagesFr);
      testI18n.activate("en");
    });

    describe("t", () => {
      it("looks up localized strings by id", () => {
        expect(testI18n.t({ id: "test.greeting" })).toEqual("Hello, Jest!");
      });

      it("handles empty strings by returning the key", () => {
        expect(testI18n.t({ id: "test.empty" })).toEqual("test.empty");
      });

      it("handles invalid keys by returning the key", () => {
        expect(testI18n.t({ id: "missing.key" })).toEqual("missing.key");
        expect(testI18n.t("foo" as any)).toEqual("foo");
      });

      it("handles invalid inputs by returning empty string", () => {
        expect(testI18n.t({ foo: 1 } as any)).toEqual("");
        expect(testI18n.t(1 as any)).toEqual("");
      });

      it("handles null/undefined inputs by throwing an error", () => {
        expect(() => testI18n.t(undefined as any)).toThrow(TypeError);
        expect(() => testI18n.t(null as any)).toThrow(TypeError);
      });
    });

    describe("activate", () => {
      it("allows changing selected locale", () => {
        expect(testI18n.t({ id: "test.greeting" })).toEqual("Hello, Jest!");
        testI18n.activate("fr");
        expect(testI18n.t({ id: "test.greeting" })).toEqual("Bonjour, Jest!");
      });
    });

    describe("load", () => {
      it("allows loading additional catalogues", () => {
        testI18n.load("zz", { "test.greeting": "Zalloz, Jest!" });
        testI18n.activate("zz");
        expect(testI18n.t({ id: "test.greeting" })).toEqual("Zalloz, Jest!");
      });

      it("combines catalogues for the same locale", () => {
        testI18n.load("zz", { "test.greeting": "Zalloz, Jest!" });
        testI18n.load("zz", { "test.another": "Zam!" });
        testI18n.activate("zz");
        expect(testI18n.t({ id: "test.greeting" })).toEqual("Zalloz, Jest!");
        expect(testI18n.t({ id: "test.another" })).toEqual("Zam!");
      });

      it("treats null/empty strings as missing keys", () => {
        testI18n.load("zz", { "test.empty": "", "test.null": null } as any);
        testI18n.activate("zz");
        expect(testI18n.t({ id: "test.empty" })).toEqual("test.empty");
        expect(testI18n.t({ id: "test.null" })).toEqual("test.null");
        expect(testI18n.t({ id: "test.missing" })).toEqual("test.missing");
      });
    });

    describe("locale getter", () => {
      it("returns the currently active locale", () => {
        expect(testI18n.locale).toEqual("en");
        testI18n.load("zz", { "test.greeting": "Zalloz, Jest!" });
        expect(testI18n.locale).toEqual("en");
        testI18n.activate("zz");
        expect(testI18n.locale).toEqual("zz");
      });
    });
  });
});
