import { produce } from "immer";

import { validateConfig } from "~/app/server-environment";
import minimalJson from "~/config/examples/minimal.json";
import fullJson from "~/config/examples/full.json";
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
      config: fullJson,
      expected: {
        isValid: true,
      },
    },
    {
      name: "multiple executable consent options",
      config: produce(fullJson, (draftConfig) => {
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
      config: produce(v2ConsentJson, (draftConfig) => {
        draftConfig.actions[0].custom_privacy_request_fields = {
          tenant_id: {
            label: "Tenant ID",
            hidden: true,
          },
        };
        draftConfig.actions[1].custom_privacy_request_fields = {
          tenant_id: {
            label: "Tenant ID",
            hidden: true,
          },
        };
      }),
      expected: {
        isValid: false,
        message:
          "A default_value is required for hidden field(s) 'tenant_id' in the action with policy_key 'default_access_policy', 'tenant_id' in the action with policy_key 'default_erasure_policy'",
      },
    },
  ];

  testCases.forEach((tc) => {
    test(tc.name, () => {
      expect(validateConfig(tc.config)).toMatchObject(tc.expected);
    });
  });
});
