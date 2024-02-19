import { FidesOptions } from "~/fides";
import {
  setupI18n,
  initializeI18n,
  updateMessagesFromFiles,
  updateMessagesFromExperience,
  detectUserLocale,
  activateBestLocaleMatch
} from "~/lib/i18n";
import type { I18n, Messages } from "~/lib/i18n";

describe("i18n-utils", () => {
  describe("initializeI18n", () => {
    it("initializes the i18n singleton with static messages and a default locale", () => {

    });
  });

  describe("updateMessagesFromFiles", () => {
    it("reads all static messages from source and loads into the i18n dictionary", () => {

    });
  });

  describe("updateMessagesFromExperience", () => {
    it("reads all messages from experience API response and loads into the i18n dictionary", () => {

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

  describe("activateBestLocaleMatch", () => {
    it("foo", () => {

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
