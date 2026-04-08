import { produce } from "immer";

import { validateConfig } from "~/common/validation";
import customFields from "~/config/examples/customFields.json";
import fullJson from "~/config/examples/full.json";
import minimalJson from "~/config/examples/minimal.json";
import v2ConsentJson from "~/config/examples/v2Consent.json";

describe("validateConfig", () => {
  const testCases = [
    {
      name: "no consent options",
      config: minimalJson,
      expected: {
        isValid: true,
      },
    },
    {
      name: "valid consent options",
      config: fullJson as any,
      expected: {
        isValid: true,
      },
    },
    {
      name: "multiple executable consent options",
      config: produce(fullJson, (draftConfig: any) => {
        draftConfig.consent.consentOptions[0].executable = true;
        draftConfig.consent.consentOptions[1].executable = true;
      }),
      expected: {
        isValid: false,
        message: "Cannot have more than one consent option be executable",
      },
    },
    {
      name: "v2 consent config",
      config: produce(v2ConsentJson, (draftConfig) => {
        draftConfig.consent.page.consentOptions[0].executable = true;
      }),
      expected: {
        isValid: true,
      },
    },
    {
      name: "multiple executable v2 consent options",
      config: produce(v2ConsentJson, (draftConfig) => {
        draftConfig.consent.page.consentOptions[0].executable = true;
        draftConfig.consent.page.consentOptions[1].executable = true;
      }),
      expected: {
        isValid: false,
        message: "Cannot have more than one consent option be executable",
      },
    },
    {
      name: "hidden fields with missing default values",
      config: customFields,
      expected: {
        isValid: false,
        message:
          "A default_value or query_param_key is required for hidden field(s) 'tenant_id' in the action with policy_key 'default_access_policy', 'tenant_id' in the action with policy_key 'default_erasure_policy'",
      },
    },
    // Required field validation
    {
      name: "missing title",
      config: produce(minimalJson, (draft: any) => {
        delete draft.title;
      }),
      expected: {
        isValid: false,
        message: "Missing required field(s): title",
      },
    },
    {
      name: "missing description",
      config: produce(minimalJson, (draft: any) => {
        delete draft.description;
      }),
      expected: {
        isValid: false,
        message: "Missing required field(s): description",
      },
    },
    {
      name: "missing logo_path",
      config: produce(minimalJson, (draft: any) => {
        delete draft.logo_path;
      }),
      expected: {
        isValid: false,
        message: "Missing required field(s): logo_path",
      },
    },
    {
      name: "empty description",
      config: produce(minimalJson, (draft: any) => {
        draft.description = "   ";
      }),
      expected: {
        isValid: false,
        message: "Missing required field(s): description",
      },
    },
    {
      name: "missing multiple required fields",
      config: produce(minimalJson, (draft: any) => {
        delete draft.title;
        delete draft.description;
      }),
      expected: {
        isValid: false,
        message: "Missing required field(s): title, description",
      },
    },
    {
      name: "empty actions array",
      config: produce(minimalJson, (draft: any) => {
        draft.actions = [];
      }),
      expected: {
        isValid: false,
        message:
          "Missing required field(s): actions (must be a non-empty array)",
      },
    },
    {
      name: "missing actions",
      config: produce(minimalJson, (draft: any) => {
        delete draft.actions;
      }),
      expected: {
        isValid: false,
        message:
          "Missing required field(s): actions (must be a non-empty array)",
      },
    },
    {
      name: "missing required action fields",
      config: produce(minimalJson, (draft: any) => {
        delete draft.actions[0].title;
        delete draft.actions[0].description;
      }),
      expected: {
        isValid: false,
        message: "Missing required field(s) in actions[0]: title, description",
      },
    },
    {
      name: "missing icon_path in action",
      config: produce(minimalJson, (draft: any) => {
        delete draft.actions[0].icon_path;
      }),
      expected: {
        isValid: false,
        message: "Missing required field(s) in actions[0]: icon_path",
      },
    },
    // URL validation
    {
      name: "valid URL fields",
      config: produce(minimalJson, (draft: any) => {
        draft.server_url_development = "http://localhost:8080";
        draft.server_url_production = "https://api.example.com";
        draft.logo_url = "https://cdn.example.com/logo.png";
      }),
      expected: {
        isValid: true,
      },
    },
    {
      name: "invalid URL field",
      config: produce(minimalJson, (draft: any) => {
        draft.server_url_development = "not-a-url";
      }),
      expected: {
        isValid: false,
        message:
          "Invalid URL(s): server_url_development (must use http or https)",
      },
    },
    {
      name: "invalid URL with wrong protocol",
      config: produce(minimalJson, (draft: any) => {
        draft.logo_url = "ftp://example.com/logo.png";
      }),
      expected: {
        isValid: false,
        message: "Invalid URL(s): logo_url (must use http or https)",
      },
    },
    {
      name: "optional URL fields omitted are valid",
      config: minimalJson,
      expected: {
        isValid: true,
      },
    },
    {
      name: "invalid link URL",
      config: produce(minimalJson, (draft: any) => {
        draft.links = [
          { label: "Privacy Policy", url: "https://example.com/privacy" },
          { label: "Bad Link", url: "not-a-url" },
        ];
      }),
      expected: {
        isValid: false,
        message:
          'Invalid URL(s) in links[1] ("Bad Link") (must use http or https)',
      },
    },
    {
      name: "valid link URLs",
      config: produce(minimalJson, (draft: any) => {
        draft.links = [
          { label: "Privacy Policy", url: "https://example.com/privacy" },
          { label: "Terms", url: "http://example.com/terms" },
        ];
      }),
      expected: {
        isValid: true,
      },
    },
  ];

  testCases.forEach((tc) => {
    test(tc.name, () => {
      expect(validateConfig(tc.config)).toMatchObject(tc.expected);
    });
  });
});
