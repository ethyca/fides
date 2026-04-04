import {
  ComponentType,
  ExperienceConfigResponse,
  ExperienceTranslationResponse,
  Layer1ButtonOption,
  SupportedLanguage,
} from "~/types/api";

import {
  defaultInitialValues,
  defaultTranslations,
  findLanguageDisplayName,
  getSelectedRegionIds,
  getTranslationFormFields,
  transformConfigResponseToCreate,
  transformTranslationResponseToCreate,
} from "./helpers";

describe("getSelectedRegionIds", () => {
  it("returns ids of selected locations", () => {
    const locations = [
      { id: "us_ca", name: "California", selected: true },
      { id: "us_ny", name: "New York", selected: false },
      { id: "fr", name: "France", selected: true },
    ];
    expect(getSelectedRegionIds(locations)).toEqual(["us_ca", "fr"]);
  });

  it("returns empty array when no locations are selected", () => {
    const locations = [
      { id: "us_ca", name: "California", selected: false },
    ];
    expect(getSelectedRegionIds(locations)).toEqual([]);
  });

  it("returns empty array when input is undefined", () => {
    expect(getSelectedRegionIds(undefined)).toEqual([]);
  });

  it("returns empty array when input is empty", () => {
    expect(getSelectedRegionIds([])).toEqual([]);
  });
});

describe("defaultInitialValues", () => {
  it("has expected default values", () => {
    expect(defaultInitialValues.name).toBe("");
    expect(defaultInitialValues.dismissable).toBe(true);
    expect(defaultInitialValues.auto_detect_language).toBe(true);
    expect(defaultInitialValues.auto_subdomain_cookie_deletion).toBe(true);
    expect(defaultInitialValues.cookie_deletion_based_on_host_domain).toBe(
      true,
    );
    expect(defaultInitialValues.allow_vendor_asset_disclosure).toBe(false);
    expect(defaultInitialValues.regions).toEqual([]);
    expect(defaultInitialValues.translations).toEqual(defaultTranslations);
  });
});

describe("defaultTranslations", () => {
  it("has a single English default translation", () => {
    expect(defaultTranslations).toHaveLength(1);
    expect(defaultTranslations[0].language).toBe(SupportedLanguage.EN);
    expect(defaultTranslations[0].is_default).toBe(true);
  });

  it("has all required button labels filled", () => {
    const t = defaultTranslations[0];
    expect(t.title).toBeTruthy();
    expect(t.description).toBeTruthy();
    expect(t.accept_button_label).toBeTruthy();
    expect(t.reject_button_label).toBeTruthy();
    expect(t.save_button_label).toBeTruthy();
    expect(t.acknowledge_button_label).toBeTruthy();
  });
});

describe("findLanguageDisplayName", () => {
  const languages = [
    { id: SupportedLanguage.EN, name: "English" },
    { id: SupportedLanguage.FR, name: "French" },
  ] as any[];

  it("returns language name when found", () => {
    const translation = { language: SupportedLanguage.FR } as any;
    expect(findLanguageDisplayName(translation, languages)).toBe("French");
  });

  it("falls back to language code when not found", () => {
    const translation = { language: "de" } as any;
    expect(findLanguageDisplayName(translation, languages)).toBe("de");
  });
});

describe("transformTranslationResponseToCreate", () => {
  it("converts null fields to undefined", () => {
    const response: ExperienceTranslationResponse = {
      language: SupportedLanguage.EN,
      is_default: true,
      title: "Title",
      description: "Desc",
      accept_button_label: "Accept",
      reject_button_label: "Reject",
      save_button_label: null,
      acknowledge_button_label: null,
      banner_title: null,
      banner_description: null,
      gpc_label: null,
      gpc_title: null,
      gpc_description: null,
      gpc_status_applied_label: null,
      gpc_status_overridden_label: null,
      purpose_header: null,
      privacy_policy_link_label: null,
      privacy_policy_url: null,
      privacy_preferences_link_label: null,
      modal_link_label: null,
    } as any;

    const result = transformTranslationResponseToCreate(response);
    expect(result.save_button_label).toBeUndefined();
    expect(result.acknowledge_button_label).toBeUndefined();
    expect(result.banner_title).toBeUndefined();
    expect(result.gpc_label).toBeUndefined();
  });

  it("preserves non-null values", () => {
    const response = {
      language: SupportedLanguage.EN,
      is_default: true,
      title: "My Title",
      description: "My Description",
      accept_button_label: "OK",
      reject_button_label: "No",
      save_button_label: "Save",
      acknowledge_button_label: null,
      banner_title: "Banner",
      banner_description: null,
      gpc_label: null,
      gpc_title: null,
      gpc_description: null,
      gpc_status_applied_label: null,
      gpc_status_overridden_label: null,
      purpose_header: null,
      privacy_policy_link_label: null,
      privacy_policy_url: null,
      privacy_preferences_link_label: null,
      modal_link_label: null,
    } as any;

    const result = transformTranslationResponseToCreate(response);
    expect(result.title).toBe("My Title");
    expect(result.accept_button_label).toBe("OK");
    expect(result.save_button_label).toBe("Save");
    expect(result.banner_title).toBe("Banner");
  });
});

describe("transformConfigResponseToCreate", () => {
  const baseResponse: ExperienceConfigResponse = {
    id: "pri_001",
    name: "Test Experience",
    component: ComponentType.BANNER_AND_MODAL,
    disabled: false,
    dismissable: true,
    created_at: "2024-01-01",
    updated_at: "2024-01-02",
    origin: "fides",
    privacy_notices: [
      { id: "notice_1", name: "Notice 1" } as any,
      { id: "notice_2", name: "Notice 2" } as any,
    ],
    translations: [],
    allow_vendor_asset_disclosure: false,
    regions: [],
  } as any;

  it("strips server-only fields", () => {
    const result = transformConfigResponseToCreate(baseResponse);
    expect(result).not.toHaveProperty("id");
    expect(result).not.toHaveProperty("created_at");
    expect(result).not.toHaveProperty("updated_at");
    expect(result).not.toHaveProperty("origin");
  });

  it("maps privacy_notices to privacy_notice_ids", () => {
    const result = transformConfigResponseToCreate(baseResponse);
    expect(result.privacy_notice_ids).toEqual(["notice_1", "notice_2"]);
    expect(result).not.toHaveProperty("privacy_notices");
  });

  it("handles empty privacy_notices", () => {
    const response = { ...baseResponse, privacy_notices: undefined };
    const result = transformConfigResponseToCreate(response as any);
    expect(result.privacy_notice_ids).toEqual([]);
  });

  it("disables vendor asset disclosure when enabled but no asset types", () => {
    const response = {
      ...baseResponse,
      allow_vendor_asset_disclosure: true,
      asset_disclosure_include_types: [],
    };
    const result = transformConfigResponseToCreate(response as any);
    expect(result.allow_vendor_asset_disclosure).toBe(false);
  });

  it("preserves vendor asset disclosure when types are present", () => {
    const response = {
      ...baseResponse,
      allow_vendor_asset_disclosure: true,
      asset_disclosure_include_types: ["cookie"],
    };
    const result = transformConfigResponseToCreate(response as any);
    expect(result.allow_vendor_asset_disclosure).toBe(true);
  });
});

describe("getTranslationFormFields", () => {
  it("includes title and description for all component types", () => {
    const types = [
      ComponentType.BANNER_AND_MODAL,
      ComponentType.MODAL,
      ComponentType.PRIVACY_CENTER,
      ComponentType.TCF_OVERLAY,
      ComponentType.HEADLESS,
    ];

    types.forEach((type) => {
      const config = getTranslationFormFields(type);
      expect(config.title).toEqual({ included: true, required: true });
      expect(config.description).toEqual({ included: true, required: true });
    });
  });

  it("includes banner fields only for banner_and_modal and tcf_overlay", () => {
    expect(
      getTranslationFormFields(ComponentType.BANNER_AND_MODAL).banner_title,
    ).toBeDefined();
    expect(
      getTranslationFormFields(ComponentType.TCF_OVERLAY).banner_title,
    ).toBeDefined();
    expect(
      getTranslationFormFields(ComponentType.MODAL).banner_title,
    ).toBeUndefined();
    expect(
      getTranslationFormFields(ComponentType.PRIVACY_CENTER).banner_title,
    ).toBeUndefined();
  });

  it("includes purpose_header only for tcf_overlay", () => {
    expect(
      getTranslationFormFields(ComponentType.TCF_OVERLAY).purpose_header,
    ).toBeDefined();
    expect(
      getTranslationFormFields(ComponentType.BANNER_AND_MODAL).purpose_header,
    ).toBeUndefined();
  });

  it("requires privacy_preferences_link_label for banner_and_modal and tcf_overlay", () => {
    expect(
      getTranslationFormFields(ComponentType.BANNER_AND_MODAL)
        .privacy_preferences_link_label,
    ).toEqual({ included: true, required: true });
    expect(
      getTranslationFormFields(ComponentType.TCF_OVERLAY)
        .privacy_preferences_link_label,
    ).toEqual({ included: true, required: true });
  });

  it("includes GPC fields for modal and banner_and_modal", () => {
    const modalConfig = getTranslationFormFields(ComponentType.MODAL);
    expect(modalConfig.gpc_label).toBeDefined();
    expect(modalConfig.gpc_title).toBeDefined();
    expect(modalConfig.gpc_description).toBeDefined();
    expect(modalConfig.gpc_status_applied_label).toBeDefined();
    expect(modalConfig.gpc_status_overridden_label).toBeDefined();

    const bannerConfig = getTranslationFormFields(
      ComponentType.BANNER_AND_MODAL,
    );
    expect(bannerConfig.gpc_label).toBeDefined();

    // TCF overlay does NOT have GPC fields
    const tcfConfig = getTranslationFormFields(ComponentType.TCF_OVERLAY);
    expect(tcfConfig.gpc_label).toBeUndefined();
  });

  it("does not include save_button_label for privacy_center as optional", () => {
    const config = getTranslationFormFields(ComponentType.PRIVACY_CENTER);
    expect(config.save_button_label).toEqual({
      included: true,
      required: true,
    });
  });
});
