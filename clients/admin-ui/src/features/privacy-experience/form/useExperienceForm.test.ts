import { renderHook } from "@testing-library/react";

import {
  ComponentType,
  ExperienceConfigResponse,
  SupportedLanguage,
} from "~/types/api";

import { defaultTranslations } from "./helpers";
import { useExperienceForm } from "./useExperienceForm";

// Mock fidesui Form to provide a minimal form instance
jest.mock("fidesui", () => ({
  Form: {
    useForm: () => [
      {
        getFieldValue: jest.fn(),
        setFieldValue: jest.fn(),
        setFieldsValue: jest.fn(),
        getFieldsValue: jest.fn(),
        validateFields: jest.fn(),
        resetFields: jest.fn(),
      },
    ],
  },
}));

describe("useExperienceForm", () => {
  describe("initialValues", () => {
    it("returns defaultInitialValues when no experience is passed", () => {
      const { result } = renderHook(() => useExperienceForm());
      expect(result.current.initialValues).toEqual(
        expect.objectContaining({
          name: "",
          dismissable: true,
          translations: defaultTranslations,
        }),
      );
    });

    it("merges passed experience over defaults", () => {
      const experience = {
        id: "pri_001",
        name: "Custom Experience",
        component: ComponentType.BANNER_AND_MODAL,
        disabled: false,
        dismissable: false,
        created_at: "2024-01-01",
        updated_at: "2024-01-02",
        origin: "fides",
        privacy_notices: [{ id: "notice_1", name: "Notice" }],
        translations: [
          {
            language: SupportedLanguage.EN,
            is_default: true,
            title: "Custom Title",
            description: "Custom Desc",
            accept_button_label: "Yes",
            reject_button_label: "No",
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
          },
        ],
        regions: [],
        allow_vendor_asset_disclosure: false,
      } as unknown as ExperienceConfigResponse;

      const { result } = renderHook(() => useExperienceForm(experience));
      expect(result.current.initialValues.name).toBe("Custom Experience");
      expect(result.current.initialValues.dismissable).toBe(false);
      expect(result.current.initialValues.privacy_notice_ids).toEqual([
        "notice_1",
      ]);
    });

    it("returns a form instance", () => {
      const { result } = renderHook(() => useExperienceForm());
      expect(result.current.form).toBeDefined();
      expect(result.current.form.validateFields).toBeDefined();
    });
  });
});
