import { FidesOptions } from "~/fides";
import {
  LOCALE_REGEX,
  setupI18n,
  initializeI18n,
  loadMessagesFromFiles,
  loadMessagesFromExperience,
  detectUserLocale,
  matchAvailableLocales,
} from "~/lib/i18n";
import messagesEn from "~/lib/i18n/locales/en/messages.json";
import messagesEs from "~/lib/i18n/locales/es/messages.json";
import type { I18n, Locale, MessageDescriptor, Messages } from "~/lib/i18n";

import mockExperienceJSON from "../../__fixtures__/mock_experience.json";
import mockExperienceNoTranslationsJSON from "../../__fixtures__/mock_experience_no_translations.json";

describe("i18n-utils", () => {
  // Define a mock implementation of the i18n singleton for tests
  const mockI18n = {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    activate: jest.fn((locale: Locale): void => {}),
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    load: jest.fn((locale: Locale, messages: Messages): void => {}),
    t: jest.fn(
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      (idOrDescriptor: string | MessageDescriptor): string => "mock translate"
    ),
  };

  // TODO: Improve this mock experience fixture type: Partial<PrivacyExperience>
  const mockExperience: any = mockExperienceJSON as any;

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
      // TODO: add additional assertions to expect the dynamic strings too
      expect(mockI18n.load).toHaveBeenCalledWith("en", messagesEn);
      expect(mockI18n.load).toHaveBeenCalledWith("es", messagesEs);
      expect(mockI18n.activate).toHaveBeenCalledWith("es");
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
        // TODO: I'm unconvinced that flattening the notices like this makes sense
        "exp.notices.pri_555.title": "Advertising Test",
        "exp.notices.pri_555.description": "Advertising Description Test",
        "exp.notices.pri_888.title": "Analytics Test",
        "exp.notices.pri_888.description": "Analytics Description Test",
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
        // TODO: I'm unconvinced that flattening the notices like this makes sense
        "exp.notices.pri_555.title": "Prueba de Publicidad",
        "exp.notices.pri_555.description":
          "Descripción de la Publicidad de Prueba",
        "exp.notices.pri_888.title": "Prueba de Analítica",
        "exp.notices.pri_888.description":
          "Descripción de la Analítica de Prueba",
      });
    });

    it("handles missing experience translations by falling back to experience_config properties", () => {
      // TODO: Improve this mock experience fixture type (Partial<PrivacyExperience>)
      const mockExperienceNoTranslations: any =
        mockExperienceNoTranslationsJSON as any;
      const updatedLocales = loadMessagesFromExperience(
        mockI18n,
        mockExperienceNoTranslations
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
        // TODO: I'm unconvinced that flattening the notices like this makes sense
        "exp.notices.pri_555.title": "Advertising Test",
        "exp.notices.pri_555.description": "Advertising Description Test",
        "exp.notices.pri_888.title": "Analytics Test",
        "exp.notices.pri_888.description": "Analytics Description Test",
      });
    });

    // TODO: this logic needs to be in the presentation layer and affect reporting
    it.skip("handles mismatched notice translations by falling back to default language", () => {});
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
    };

    const testMessagesFr: Messages = {
      "test.greeting": "Bonjour, Jest!",
      "test.phrase": "Déplacez-vous délibérément et réparez les choses",
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
    });
  });
});
