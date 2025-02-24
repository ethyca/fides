import {
  ExperienceConfig,
  FidesExperienceTranslationOverrides,
  FidesInitOptions,
  PrivacyExperience,
  PrivacyNoticeWithPreference,
} from "~/fides";
import {
  areLocalesEqual,
  DEFAULT_LOCALE,
  DEFAULT_MODAL_LINK_LABEL,
  detectUserLocale,
  extractDefaultLocaleFromExperience,
  getCurrentLocale,
  I18n,
  initializeI18n,
  Language,
  loadMessagesFromExperience,
  loadMessagesFromFiles,
  loadMessagesFromGVLTranslations,
  Locale,
  LOCALE_REGEX,
  localizeModalLinkText,
  matchAvailableLocales,
  MessageDescriptor,
  messageExists,
  Messages,
  selectBestExperienceConfigTranslation,
  selectBestNoticeTranslation,
  setupI18n,
} from "~/lib/i18n";
import messagesEn from "~/lib/i18n/locales/en/messages.json";
import messagesEs from "~/lib/i18n/locales/es/messages.json";
import messagesTcfEn from "~/lib/tcf/i18n/locales/en/messages-tcf.json";
import messagesTcfEs from "~/lib/tcf/i18n/locales/es/messages-tcf.json";
import { loadTcfMessagesFromFiles } from "~/lib/tcf/i18n/tcf-i18n-utils";

import mockExperienceJSON from "../../__fixtures__/mock_experience.json";
import mockGVLTranslationsJSON from "../../__fixtures__/mock_gvl_translations.json";

describe("i18n-utils", () => {
  beforeAll(() => {
    window.fidesDebugger = () => {};
  });
  // Define a mock implementation of the i18n singleton for tests
  let mockCurrentLocale = "";
  let mockDefaultLocale = DEFAULT_LOCALE;
  let mockAvailableLanguages: Language[] = [
    { locale: "en", label_en: "English", label_original: "English" },
    { locale: "es", label_en: "Spanish", label_original: "Español" },
  ];
  const mockI18nCatalogLoad = [
    {
      "exp.accept_button_label": "Accept Test",
      "exp.acknowledge_button_label": "Acknowledge Test",
      "exp.banner_description": "Banner Description Test",
      "exp.banner_title": "Banner Title Test",
      "exp.description": "Description Test",
      "exp.modal_link_label": "Link Label Test",
      "exp.privacy_policy_link_label": "Privacy Policy Test",
      "exp.privacy_policy_url": "https://privacy.example.com/",
      "exp.privacy_preferences_link_label": "Manage Preferences Test",
      "exp.reject_button_label": "Reject Test",
      "exp.save_button_label": "Save Test",
      "exp.title": "Title Test",
    },
    {
      "exp.accept_button_label": "Aceptar Prueba",
      "exp.acknowledge_button_label": "Reconocer Prueba",
      "exp.banner_description": "Descripción del Banner de Prueba",
      "exp.banner_title": "Título del Banner de Prueba",
      "exp.description": "Descripción de la Prueba",
      "exp.modal_link_label": "Prueba de etiqueta",
      "exp.privacy_policy_link_label": "Política de Privacidad de Prueba",
      "exp.privacy_policy_url": "https://privacy.example.com/es",
      "exp.privacy_preferences_link_label":
        "Administrar Preferencias de Prueba",
      "exp.reject_button_label": "Rechazar Prueba",
      "exp.save_button_label": "Guardar Prueba",
      "exp.title": "Título de la Prueba",
    },
  ];

  const mockI18n = {
    activate: jest.fn((locale: Locale): void => {
      mockCurrentLocale = locale;
    }),

    setAvailableLanguages: jest.fn((languages: Language[]): void => {
      mockAvailableLanguages = languages;
    }),

    get availableLanguages(): Language[] {
      return mockAvailableLanguages;
    },

    getDefaultLocale: jest.fn((): Locale => mockDefaultLocale),

    setDefaultLocale: jest.fn((locale: Locale): void => {
      mockDefaultLocale = locale;
    }),

    get locale(): Locale {
      return mockCurrentLocale;
    },

    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    load: jest.fn((locale: Locale, messages: Messages): void => {}),

    t: jest.fn((idOrDescriptor: string | MessageDescriptor): string => {
      switch (mockCurrentLocale) {
        case "en":
          return "mock translation";
        case "es":
          return "traducción simulada";
        default:
          return idOrDescriptor.toString();
      }
    }),
  };

  const mockExperience: Partial<PrivacyExperience> = mockExperienceJSON as any;

  afterEach(() => {
    mockI18n.activate.mockClear();
    mockI18n.load.mockClear();
    mockI18n.t.mockClear();
    mockCurrentLocale = "";
    mockDefaultLocale = DEFAULT_LOCALE;
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

    it("changes the fallback default locale based on the first is_default translation in the experience", () => {
      // Make a deep copy of the mock experience using a dirty JSON serialization trick
      // NOTE: This is why lodash exists, but I'm not going to install it just for this! :)
      const mockExpDifferentDefault = JSON.parse(
        JSON.stringify(mockExperience),
      );
      mockExpDifferentDefault.experience_config.translations[0].is_default =
        false;
      mockExpDifferentDefault.experience_config.translations[1].is_default =
        true; // sets "es" to default

      const mockNavigator: Partial<Navigator> = {
        language: "fr-CA", // not a match for either en or es
      };

      initializeI18n(mockI18n, mockNavigator, mockExpDifferentDefault);
      expect(mockI18n.load).toHaveBeenCalledWith("en", messagesEn);
      expect(mockI18n.load).toHaveBeenCalledWith("es", messagesEs);
      expect(mockI18n.setDefaultLocale).toHaveBeenCalledWith("es");
      expect(mockI18n.setAvailableLanguages).toHaveBeenCalledWith(
        mockAvailableLanguages,
      );
      expect(mockI18n.activate).toHaveBeenCalledWith("es");
    });

    it("handles i18n initialization when translation isn't available (yet)", () => {
      const mockNavigator: Partial<Navigator> = {
        language: "fr",
      };
      const mockExpMinimalCached = JSON.parse(JSON.stringify(mockExperience));
      mockExpMinimalCached.experience_config.translations.splice(0, 1);
      mockExpMinimalCached.available_locales.push("fr");
      initializeI18n(mockI18n, mockNavigator, mockExpMinimalCached);
      expect(mockI18n.setDefaultLocale).toHaveBeenCalledWith("es");
    });
  });

  describe("loadMessagesFromFiles", () => {
    it("reads all static messages from source and loads into the i18n catalog", () => {
      const updatedLocales = loadMessagesFromFiles(mockI18n);

      // Check the updated locales list is what we expect
      const EXPECTED_NUM_STATIC_LOCALES = 40; // NOTE: manually update this as new locales added
      expect(updatedLocales).toHaveLength(EXPECTED_NUM_STATIC_LOCALES);
      expect(updatedLocales).toContain("en");
      expect(mockI18n.load).toHaveBeenCalledTimes(EXPECTED_NUM_STATIC_LOCALES);

      // Verify a few of our expected locales match their expected catalogues, too
      expect(mockI18n.load).toHaveBeenCalledWith("en", messagesEn);
      expect(mockI18n.load).toHaveBeenCalledWith("es", messagesEs);

      // Sanity-check a few of the loaded messages match our expected static strings
      const [, loadedMessagesEn] =
        mockI18n.load.mock.calls.find(([locale]) => locale === "en") || [];
      const [, loadedMessagesEs] =
        mockI18n.load.mock.calls.find(([locale]) => locale === "es") || [];
      expect(loadedMessagesEn).toMatchObject({
        "static.gpc": "Global Privacy Control",
        "static.gpc.status.applied": "Applied",
      });
      expect(loadedMessagesEs).toMatchObject({
        "static.gpc": "Control de privacidad global",
        "static.gpc.status.applied": "Aplicado",
      });

      // Check that TCF strings are not loaded
      expect(loadedMessagesEn).not.toHaveProperty(["static.tcf.consent"]);
      expect(loadedMessagesEs).not.toHaveProperty(["static.tcf.consent"]);
    });
  });

  describe("loadTcfMessagesFromFiles", () => {
    it("reads all TCF-specific static messages from source and loads into the i18n catalog", () => {
      const updatedLocales = loadTcfMessagesFromFiles(mockI18n);

      // Check the updated locales list is what we expect
      const EXPECTED_NUM_STATIC_LOCALES = 40; // NOTE: manually update this as new locales added
      expect(updatedLocales).toHaveLength(EXPECTED_NUM_STATIC_LOCALES);
      expect(updatedLocales).toContain("en");
      expect(mockI18n.load).toHaveBeenCalledTimes(EXPECTED_NUM_STATIC_LOCALES);

      // Verify a few of our expected locales match their expected catalogues, too
      expect(mockI18n.load).toHaveBeenCalledWith("en", messagesTcfEn);
      expect(mockI18n.load).toHaveBeenCalledWith("es", messagesTcfEs);

      // Sanity-check a few of the loaded messages match our expected static strings
      const [, loadedMessagesEn] =
        mockI18n.load.mock.calls.find(([locale]) => locale === "en") || [];
      const [, loadedMessagesEs] =
        mockI18n.load.mock.calls.find(([locale]) => locale === "es") || [];
      expect(loadedMessagesEn).toMatchObject({
        "static.tcf.consent": "Consent",
        "static.tcf.features": "Features",
      });
      expect(loadedMessagesEs).toMatchObject({
        "static.tcf.consent": "Consentimiento",
        "static.tcf.features": "Características",
      });

      // Check that regular static strings are not loaded
      expect(loadedMessagesEn).not.toHaveProperty(["static.gpc"]);
      expect(loadedMessagesEs).not.toHaveProperty(["static.gpc"]);
    });
  });

  describe("loadMessagesFromExperience", () => {
    it("reads all messages from experience API response and loads into the i18n catalog", () => {
      loadMessagesFromExperience(mockI18n, mockExperience);
      const EXPECTED_NUM_TRANSLATIONS = 2;
      expect(mockI18n.load).toHaveBeenCalledTimes(EXPECTED_NUM_TRANSLATIONS);
      expect(mockI18n.load).toHaveBeenCalledWith("en", mockI18nCatalogLoad[0]);
      expect(mockI18n.load).toHaveBeenCalledWith("es", mockI18nCatalogLoad[1]);
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

    it("handles missing experience_config translations by falling back to legacy properties", () => {
      // Make a deep copy of the mock experience using a dirty JSON serialization trick
      // NOTE: This is why lodash exists, but I'm not going to install it just for this! :)
      const mockExpNoTranslations = JSON.parse(JSON.stringify(mockExperience));

      // Edit the experience data to match the legacy format (w/o translations)
      delete mockExpNoTranslations.experience_config.translations;
      mockExpNoTranslations.available_locales = ["en"];

      // Load the "no translations" version of the experience and run tests
      loadMessagesFromExperience(mockI18n, mockExpNoTranslations as any);

      const EXPECTED_NUM_TRANSLATIONS = 1;
      expect(mockI18n.load).toHaveBeenCalledTimes(EXPECTED_NUM_TRANSLATIONS);
      expect(mockI18n.load).toHaveBeenCalledWith("en", mockI18nCatalogLoad[0]);
    });

    it("sets overrides experience_config translations when locale matches", () => {
      const experienceTranslationOverrides: Partial<FidesExperienceTranslationOverrides> =
        {
          title: "My override title",
          description: "My override description",
          override_language: "en",
        };
      loadMessagesFromExperience(
        mockI18n,
        mockExperience,
        experienceTranslationOverrides,
      );
      const EXPECTED_NUM_TRANSLATIONS = 2;
      expect(mockI18n.load).toHaveBeenCalledTimes(EXPECTED_NUM_TRANSLATIONS);
      expect(mockI18n.load).toHaveBeenCalledWith("en", {
        ...mockI18nCatalogLoad[0],
        ...{
          "exp.description": experienceTranslationOverrides.description,
          "exp.title": experienceTranslationOverrides.title,
        },
      });
      expect(mockI18n.load).toHaveBeenCalledWith("es", mockI18nCatalogLoad[1]);
    });

    it("does not set overrides experience_config translations when no locale match", () => {
      const experienceTranslationOverrides: Partial<FidesExperienceTranslationOverrides> =
        {
          title: "My override title",
          description: "My override description",
          override_language: "ja",
        };
      loadMessagesFromExperience(
        mockI18n,
        mockExperience,
        experienceTranslationOverrides,
      );
      const EXPECTED_NUM_TRANSLATIONS = 2;
      expect(mockI18n.load).toHaveBeenCalledTimes(EXPECTED_NUM_TRANSLATIONS);
      expect(mockI18n.load).toHaveBeenCalledWith("en", mockI18nCatalogLoad[0]);
      expect(mockI18n.load).toHaveBeenCalledWith("es", mockI18nCatalogLoad[1]);
    });

    it("always override privacy_policy_url, even if locale doesn't match", () => {
      const experienceTranslationOverrides: Partial<FidesExperienceTranslationOverrides> =
        {
          title: "My override title",
          description: "My override description",
          privacy_policy_url: "https://example.com/privacy",
          override_language: "ja",
        };
      loadMessagesFromExperience(
        mockI18n,
        mockExperience,
        experienceTranslationOverrides,
      );
      const EXPECTED_NUM_TRANSLATIONS = 2;
      expect(mockI18n.load).toHaveBeenCalledTimes(EXPECTED_NUM_TRANSLATIONS);
      expect(mockI18n.load).toHaveBeenCalledWith("en", {
        ...mockI18nCatalogLoad[0],
        "exp.privacy_policy_url":
          experienceTranslationOverrides.privacy_policy_url,
      });
      expect(mockI18n.load).toHaveBeenCalledWith("es", {
        ...mockI18nCatalogLoad[1],
        "exp.privacy_policy_url":
          experienceTranslationOverrides.privacy_policy_url,
      });
    });

    describe("when loading from a tcf_overlay experience", () => {
      it("reads all messages from gvl translations API response and loads into the i18n catalog", () => {
        // Mock out a partial response for a tcf_overlay including translations
        const mockExpWithGVL = JSON.parse(JSON.stringify(mockExperience));
        mockExpWithGVL.experience_config.component = "tcf_overlay";

        // Load all the translations
        loadMessagesFromGVLTranslations(mockI18n, mockGVLTranslationsJSON, [
          "en",
          "es",
        ]);

        const EXPECTED_NUM_TRANSLATIONS = 2;
        expect(mockI18n.load).toHaveBeenCalledTimes(EXPECTED_NUM_TRANSLATIONS);
        const [, loadedMessagesEn] = mockI18n.load.mock.calls[0];
        const [, loadedMessagesEs] = mockI18n.load.mock.calls[1];

        // Confirm that the English GVL translations are loaded
        const expectedMessagesEn: Record<string, RegExp> = {
          // Example purposes
          "exp.tcf.purposes.1.name": /^Store and\/or access/,
          "exp.tcf.purposes.1.description": /^Cookies, device or similar/,
          "exp.tcf.purposes.1.illustrations.0": /^Most purposes explained/,
          "exp.tcf.purposes.11.name": /^Use limited data to select content/,
          "exp.tcf.purposes.11.description": /^Content presented to you/,
          "exp.tcf.purposes.11.illustrations.1": /^A sports news mobile/,
          // Example special purpose
          "exp.tcf.specialPurposes.2.name": /^Deliver and present/,
          "exp.tcf.specialPurposes.2.description": /^Certain information /,
          "exp.tcf.specialPurposes.2.illustrations.0": /^Clicking on a link/,
          // Example feature
          "exp.tcf.features.3.name": /^Identify devices based on information/,
          "exp.tcf.features.3.description": /^Your device might be /,
          // Example special feature
          "exp.tcf.specialFeatures.1.name": /^Use precise geolocation data/,
          "exp.tcf.specialFeatures.1.description": /^With your acceptance/,
          // Example stack
          "exp.tcf.stacks.40.name": /^Personalised advertising.*development$/,
          "exp.tcf.stacks.40.description": /^Advertising can be personalised/,
          // Example data category
          "exp.tcf.dataCategories.9.name": /^Precise location data$/,
          "exp.tcf.dataCategories.9.description": /^Your precise location/,
        };
        Object.entries(expectedMessagesEn).forEach(([id, regex]) => {
          expect(loadedMessagesEn).toHaveProperty([id]);
          expect(loadedMessagesEn[id]).toMatch(regex);
        });

        // Confirm that the Spanish GVL translations are loaded
        const expectedMessagesEs: Record<string, RegExp> = {
          // Example purposes
          "exp.tcf.purposes.1.name": /^Almacenar la información/,
          "exp.tcf.purposes.1.description": /^Las cookies, los identificadores/,
          "exp.tcf.purposes.1.illustrations.0": /^La mayoría de las finalid/,
          "exp.tcf.purposes.11.name": /^Uso de datos limitados con el objetivo/,
          "exp.tcf.purposes.11.description": /^El contenido que se presenta/,
          "exp.tcf.purposes.11.illustrations.1": /^Una aplicación móvil/,
          // Example special purpose
          "exp.tcf.specialPurposes.2.name": /^Ofrecer y presentar publicidad/,
          "exp.tcf.specialPurposes.2.description": /^Cierta información/,
          "exp.tcf.specialPurposes.2.illustrations.0": /^Hacer clic en el/,
          // Example feature
          "exp.tcf.features.3.name": /^Identificación de dispositivos/,
          "exp.tcf.features.3.description": /^Tu dispositivo podría/,
          // Example special feature
          "exp.tcf.specialFeatures.1.name": /^Utilizar datos de localización/,
          "exp.tcf.specialFeatures.1.description": /^Al contar con tu/,
          // Example stack
          "exp.tcf.stacks.40.name": /^Publicidad personalizada.*de servicios$/,
          "exp.tcf.stacks.40.description": /^La publicidad puede personaliza/,
          // Example data category
          "exp.tcf.dataCategories.9.name": /^Datos de localización geográfica/,
          "exp.tcf.dataCategories.9.description": /^Tu ubicación precisa/,
        };
        Object.entries(expectedMessagesEs).forEach(([id, regex]) => {
          expect(loadedMessagesEs[id]).toMatch(regex);
        });

        // Quick helper function to count the number of unique records
        // (purposes, features, etc.) in the translated messages
        const getRecordCounts = (messages: Messages) => {
          const regexes = {
            purposes: /exp\.tcf\.purposes\.\d+\.name/,
            specialPurposes: /exp\.tcf\.specialPurposes\.\d+\.name/,
            features: /exp\.tcf\.features\.\d+\.name/,
            specialFeatures: /exp\.tcf\.specialFeatures\.\d+\.name/,
            stacks: /exp\.tcf\.stacks\.\d+\.name/,
            dataCategories: /exp\.tcf\.dataCategories\.\d+\.name/,
          };
          const recordCounts: Record<string, number> = {};
          const ids = Object.keys(messages);
          Object.entries(regexes).forEach(([type, regex]) => {
            const count = ids.filter((id) => id.match(regex)).length;
            recordCounts[type] = count;
          });
          return recordCounts;
        };

        // Confirm the translated record counts
        const expectedCounts = {
          purposes: 11,
          specialPurposes: 2,
          features: 3,
          specialFeatures: 2,
          stacks: 45,
          dataCategories: 11,
        };
        expect(getRecordCounts(loadedMessagesEn)).toMatchObject(expectedCounts);
        expect(getRecordCounts(loadedMessagesEs)).toMatchObject(expectedCounts);
      });
    });
  });

  describe("extractDefaultLocaleFromExperience", () => {
    it("returns the locale of the first 'is_default' translation from experience_config", () => {
      expect(extractDefaultLocaleFromExperience(mockExperience)).toEqual("en");

      expect(
        extractDefaultLocaleFromExperience({
          experience_config: {
            translations: [
              { language: "en", is_default: false },
              { language: "es", is_default: false },
              { language: "fr", is_default: true },
              { language: "zh", is_default: false },
            ],
          },
        } as Partial<PrivacyExperience>),
      ).toEqual("fr");

      // Check for multiple 'is_default' translations
      expect(
        extractDefaultLocaleFromExperience({
          experience_config: {
            translations: [
              { language: "en", is_default: false },
              { language: "es", is_default: true },
              { language: "fr", is_default: true },
              { language: "zh", is_default: false },
            ],
          },
        } as Partial<PrivacyExperience>),
      ).toEqual("es");
    });

    it("returns undefined if no 'is_default' translations exist in experience_config", () => {
      expect(
        extractDefaultLocaleFromExperience({
          experience_config: {
            translations: [
              { language: "en", is_default: false },
              { language: "es", is_default: false },
              { language: "fr", is_default: false },
              { language: "zh", is_default: false },
            ],
          },
        } as Partial<PrivacyExperience>),
      ).toBeUndefined();
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
      const mockOptions: Partial<FidesInitOptions> = {
        fidesLocale: "fr",
      };
      expect(detectUserLocale(mockNavigator, mockOptions.fidesLocale)).toEqual(
        "fr",
      );
    });

    it("returns the browser locale if locale is provided but undefined", () => {
      const mockOptions: Partial<FidesInitOptions> = {};
      expect(detectUserLocale(mockNavigator, mockOptions.fidesLocale)).toEqual(
        "es",
      );
    });

    it("returns the default locale if provided and browser locale is missing", () => {
      expect(detectUserLocale({}, undefined, "fr")).toEqual("fr");
    });
  });

  describe("areLocalesEqual", () => {
    it("performs a case-insensitive match and treats underscore- & dash-separated locales as equal", () => {
      expect(areLocalesEqual("en", "en")).toEqual(true);
      expect(areLocalesEqual("en", "EN")).toEqual(true);
      expect(areLocalesEqual("en-US", "en-US")).toEqual(true);
      expect(areLocalesEqual("en-US", "EN-us")).toEqual(true);
      expect(areLocalesEqual("en-US", "en_US")).toEqual(true);
      expect(areLocalesEqual("en-US", "en_us")).toEqual(true);
      expect(areLocalesEqual("en", "fr")).toEqual(false);
      expect(areLocalesEqual("en", "en-US")).toEqual(false);
      expect(areLocalesEqual("fr-CA", "fr-CA-Foo")).toEqual(false);
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

    it("falls back to a user-specified default language when no match is found", () => {
      const userDefaultLocale = "fr";
      const availableLocales = ["en", "es", "fr"];
      expect(
        matchAvailableLocales("zh", availableLocales, userDefaultLocale),
      ).toEqual("fr");
      expect(
        matchAvailableLocales("foo", availableLocales, userDefaultLocale),
      ).toEqual("fr");
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
      expect(selectBestNoticeTranslation(mockI18n, mockNotice)).toHaveProperty(
        "language",
        "es",
      );
    });

    it("falls back to the default locale if an exact match isn't available", () => {
      mockCurrentLocale = "zh";
      mockDefaultLocale = "en";
      expect(selectBestNoticeTranslation(mockI18n, mockNotice)).toHaveProperty(
        "language",
        "en",
      );

      mockDefaultLocale = "es";
      expect(selectBestNoticeTranslation(mockI18n, mockNotice)).toHaveProperty(
        "language",
        "es",
      );
    });

    it("falls back to the first locale if neither exact match nor default locale are available", () => {
      const mockNoticeNoEnglish: PrivacyNoticeWithPreference = JSON.parse(
        JSON.stringify(mockNotice),
      );
      mockNoticeNoEnglish.translations = [mockNotice.translations[1]];
      expect(mockNoticeNoEnglish.translations.map((e) => e.language)).toEqual([
        "es",
      ]);
      mockCurrentLocale = "zh";
      mockDefaultLocale = "en";
      expect(
        selectBestNoticeTranslation(mockI18n, mockNoticeNoEnglish),
      ).toHaveProperty("language", "es");
    });

    it("returns null for invalid/missing translations", () => {
      expect(selectBestNoticeTranslation(mockI18n, null as any)).toBeNull();
      expect(
        selectBestNoticeTranslation(mockI18n, { translations: [] } as any),
      ).toBeNull();
      expect(
        selectBestNoticeTranslation(mockI18n, { translations: null } as any),
      ).toBeNull();
      expect(
        selectBestNoticeTranslation(mockI18n, {
          translations: undefined,
        } as any),
      ).toBeNull();
    });
  });

  describe("selectBestExperienceConfigTranslation", () => {
    let mockExperienceConfig: ExperienceConfig;

    beforeEach(() => {
      // Assert our test data is valid, so that Typescript is happy!
      if (!mockExperience.experience_config) {
        throw new Error("Invalid mock experience test data!");
      }
      mockExperienceConfig = mockExperience.experience_config;
    });

    it("selects an exact match for current locale if available", () => {
      mockCurrentLocale = "es";
      expect(
        selectBestExperienceConfigTranslation(mockI18n, mockExperienceConfig),
      ).toHaveProperty("language", "es");
    });

    it("falls back to the default locale if an exact match isn't available", () => {
      mockCurrentLocale = "zh";
      mockDefaultLocale = "en";
      expect(
        selectBestExperienceConfigTranslation(mockI18n, mockExperienceConfig),
      ).toHaveProperty("language", "en");

      mockDefaultLocale = "es";
      expect(
        selectBestExperienceConfigTranslation(mockI18n, mockExperienceConfig),
      ).toHaveProperty("language", "es");
    });

    it("falls back to the first locale if neither exact match nor default locale are available", () => {
      const mockExpNoEnglish: ExperienceConfig = JSON.parse(
        JSON.stringify(mockExperienceConfig),
      );
      mockExpNoEnglish.translations = [mockExpNoEnglish.translations[1]];
      expect(mockExpNoEnglish.translations.map((e) => e.language)).toEqual([
        "es",
      ]);
      mockCurrentLocale = "zh";
      expect(
        selectBestExperienceConfigTranslation(mockI18n, mockExpNoEnglish),
      ).toHaveProperty("language", "es");
    });

    it("returns null for invalid/missing translations", () => {
      expect(
        selectBestExperienceConfigTranslation(mockI18n, null as any),
      ).toBeNull();
      expect(
        selectBestExperienceConfigTranslation(mockI18n, {
          translations: [],
        } as any),
      ).toBeNull();
      expect(
        selectBestExperienceConfigTranslation(mockI18n, {
          translations: null,
        } as any),
      ).toBeNull();
      expect(
        selectBestExperienceConfigTranslation(mockI18n, {
          translations: undefined,
        } as any),
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
          expect(Array.from(match)).toEqual(expectedResults);
        } else {
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

  describe("localizeModalLinkText", () => {
    it("should return the localized label when localization is not disabled", () => {
      mockI18n.activate("es");
      const result = localizeModalLinkText(false, mockI18n, mockExperience);
      expect(result).toBe("traducción simulada");
    });

    it("should return the default label when localization is not disabled and no matching locale is found", () => {
      mockI18n.activate("fr");
      const result = localizeModalLinkText(false, mockI18n, mockExperience);
      expect(result).toBe(DEFAULT_MODAL_LINK_LABEL);
    });

    it("should return the default locale label when localization is disabled and no matching locale is found", () => {
      mockI18n.activate("en");
      mockI18n.getDefaultLocale.mockReturnValue("fr");
      mockI18n.getDefaultLocale.mockReturnValue(DEFAULT_LOCALE);
      const result = localizeModalLinkText(true, mockI18n, mockExperience);
      expect(result).toBe("Link Label Test");
    });

    it("should return the label for the default locale when localization is disabled and a matching locale is found", () => {
      mockI18n.activate("en");
      mockI18n.getDefaultLocale.mockReturnValue("es");
      const result = localizeModalLinkText(true, mockI18n, mockExperience);
      expect(result).toBe("Prueba de etiqueta");
    });

    it("should return the default label when localization is disabled and no matching locale is found", () => {
      mockI18n.activate("en");
      mockI18n.getDefaultLocale.mockReturnValue("fr");
      const result = localizeModalLinkText(true, mockI18n, mockExperience);
      expect(result).toBe(DEFAULT_MODAL_LINK_LABEL);
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
      "component" | "experience_config" | "privacy_notices" | "gvl"
    > & {
      component: string;
      experience_config: Omit<
        ExperienceConfig,
        "component" | "layer1_button_options"
      > & {
        component: string;
        layer1_button_options: string;
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
        "banner_and_modal",
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

      it("when loading the same message id multiple times, replaces existing messages with newer ones", () => {
        testI18n.load("zz", { "test.greeting": "Zalloz, Jest!" });
        testI18n.activate("zz");
        testI18n.load("zz", { "test.greeting": "Zalloz zagain, Jest!" });
        testI18n.load("zz", { "test.greeting": "Zalloz ze final zone, Jest!" });
        expect(testI18n.t({ id: "test.greeting" })).toEqual(
          "Zalloz ze final zone, Jest!",
        );
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
      it("allows getting but not setting the currently active locale", () => {
        expect(testI18n.locale).toEqual("en");
        expect(testI18n.locale).toEqual("en");
        // eslint-disable-next-line no-return-assign
        expect(() => ((testI18n as any).locale = "zz")).toThrow(TypeError);
        expect(testI18n.locale).toEqual("en");

        // Change the actual locale using load & activate
        testI18n.load("zz", { "test.greeting": "Zalloz, Jest!" });
        expect(testI18n.locale).toEqual("en");
        testI18n.activate("zz");
        expect(testI18n.locale).toEqual("zz");
      });
    });

    describe("getDefaultLocale & setDefaultLocale methods", () => {
      /**
       * NOTE: Modifying the default locale is *not* supported by LinguiJS, so
       * this would need to be re-implemented carefully! This default locale
       * should typically not be needed for i18n purposes - instead, the current
       * locale should be used! However, in our application we need to provide
       * fallback behavior in some scenarios when the current locale cannot be
       * used, and in those cases we want the default locale to (sometimes!) not
       * just be English.
       *
       * For example, see selectBestNoticeTranslation() that needs a fallback to
       * a default locale in some scenarios.
       */
      it("allows getting & setting the default locale", () => {
        expect(testI18n.getDefaultLocale()).toEqual("en");
        expect(testI18n.setDefaultLocale("es")).toBeUndefined();
        expect(testI18n.getDefaultLocale()).toEqual("es");
      });
    });
  });
});
