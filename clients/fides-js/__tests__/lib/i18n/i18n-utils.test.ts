import { FidesOptions, PrivacyExperience } from "~/fides";
import {
  setupI18n,
  initializeI18n,
  updateMessagesFromFiles,
  updateMessagesFromExperience,
  detectUserLocale,
  matchAvailableLocales,
  i18n,
} from "~/lib/i18n";
import messagesEn from "~/lib/i18n/locales/en/messages.json";
import messagesFr from "~/lib/i18n/locales/fr/messages.json";
import type { I18n, Locale, MessageDescriptor, Messages } from "~/lib/i18n";

describe("i18n-utils", () => {
  // Define a mock implementation of the i18n singleton for tests
  const mockI18n  = {
    activate: jest.fn((locale: Locale): void => {}),
    load: jest.fn((locale: Locale, messages: Messages): void => {}),
    t: jest.fn((idOrDescriptor: string | MessageDescriptor): string => "mock translate"),
  };

  // TODO: unskip when ready
  describe.skip("initializeI18n", () => {
    it("initializes the i18n singleton with static messages and a default locale", () => {
      initializeI18n(mockI18n);
      expect(mockI18n.load.mock.calls).toHaveBeenCalled();
      expect(mockI18n.activate.mock.calls).toHaveBeenCalled();
    });
  });

  // TODO: unskip when ready
  describe.skip("updateMessagesFromFiles", () => {
    it("reads all static messages from source and loads into the i18n dictionary", () => {
      updateMessagesFromFiles(mockI18n);
      const EXPECTED_NUM_LOCALE_FILES = 2; // TODO: make this autodetect from lib/i18n/locales
      expect(mockI18n.load.mock.calls).toHaveBeenCalledTimes(EXPECTED_NUM_LOCALE_FILES);

      // Check the first & second locales are what we expect
      const [ firstLocale, firstMessages ] = mockI18n.load.mock.calls[0];
      const [ secondLocale, secondMessages ] = mockI18n.load.mock.calls[1];
      expect(firstLocale).toEqual("en");
      expect(firstMessages).toEqual(messagesEn);
      expect(secondLocale).toEqual("fr");
      expect(secondMessages).toEqual(messagesFr);
    });
  });

  // TODO: unskip when ready
  describe.skip("updateMessagesFromExperience", () => {
    // TODO: update with translation values
    const mockExperience: PrivacyExperience = {
      "region": "us_ca",
      "id": "pri_abc",
      "created_at": "2024-01-01T12:00:00",
      "updated_at": "2024-01-01T12:00:00",
    };

    it("reads all messages from experience API response and loads into the i18n dictionary", () => {
      updateMessagesFromExperience(mockI18n, mockExperience);
      const EXPECTED_NUM_TRANSLATIONS = 1;
      expect(mockI18n.load.mock.calls).toHaveBeenCalledTimes(EXPECTED_NUM_TRANSLATIONS);
      const [ locale, messages ] = mockI18n.load.mock.calls[0];
      expect(locale).toEqual("zh");
      // TODO: update expected format
      expect(messages).toEqual({
        "experience.accept_button_label": "foo",
        "experience.acknowledge_button_label": "foo",
        "experience.description": "foo",
        "experience.privacy_policy_link_label": "foo",
        "experience.reject_button_label": "foo",
        "experience.save_button_label": "foo",
        "experience.title": "foo",
      });
    });
  });

  // TODO: unskip when ready
  describe.skip("detectUserLocale", () => {
    const mockNavigator: Partial<Navigator> = {
      language: "es"
    };

    it("returns the browser locale by default", () => {
      expect(detectUserLocale(mockNavigator)).toEqual("es");
    });

    it("returns the fides_locale override if present in options", () => {
      const mockOptions: Partial<FidesOptions> = {
        // TODO: update types
        // fidesLocale: "fr",
      };
      expect(detectUserLocale(mockNavigator, mockOptions)).toEqual("fr");
    });
  });

  // TODO: unskip when ready
  describe.skip("matchAvailableLocales", () => {
    it("returns an exact match when able", () => {
      const availableLocales = ["en", "es", "fr-CA"];
      expect(matchAvailableLocales("fr-CA", availableLocales)).toEqual("fr-CA");
      expect(matchAvailableLocales("es", availableLocales)).toEqual("es");
    });

    it("falls back to langauge when language+region is not available", () => {
      const availableLocales = ["en", "es", "fr"];
      expect(matchAvailableLocales("fr-CA", availableLocales)).toEqual("fr");
      expect(matchAvailableLocales("es-ES", availableLocales)).toEqual("es");
    });

    it("falls back to default language when no match is found", () => {
      const availableLocales = ["en", "es", "fr"];
      expect(matchAvailableLocales("zh", availableLocales)).toEqual("en");
      expect(matchAvailableLocales("foo", availableLocales)).toEqual("en");
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

  describe("when loading a test messages dictionary", () => {
    const messagesEn: Messages = {
      "test.greeting": "Hello, Jest!",
      "test.phrase": "Move purposefully and fix things",
    };

    const messagesFr: Messages = {
      "test.greeting": "Bonjour, Jest!",
      "test.phrase": "Déplacez-vous délibérément et réparez les choses",
    };

    let testI18n: I18n;

    beforeEach(() => {
      testI18n = setupI18n();
      testI18n.load("en", messagesEn);
      testI18n.load("fr", messagesFr);
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
      it("allows loading additional dictionaries", () => {
        testI18n.load("zz", { "test.greeting": "Zalloz, Jest!" });
        testI18n.activate("zz");
        expect(testI18n.t({ id: "test.greeting" })).toEqual("Zalloz, Jest!");
      });
    });
  });
});
