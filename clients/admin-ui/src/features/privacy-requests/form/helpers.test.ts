import { PrivacyRequestOption } from "~/types/api";

import { findActionFromPolicyKey, generateFormRulesFromAction } from "./helpers";

const baseAction: PrivacyRequestOption = {
  icon_path: "/icon.svg",
  title: "Access your data",
  description: "Access request",
  policy_key: "default_access_policy",
};

describe("findActionFromPolicyKey", () => {
  const actions: PrivacyRequestOption[] = [
    { ...baseAction, policy_key: "access_policy" },
    { ...baseAction, policy_key: "erasure_policy", title: "Erase your data" },
  ];

  it("returns the matching action", () => {
    expect(findActionFromPolicyKey("erasure_policy", actions)?.title).toBe(
      "Erase your data",
    );
  });

  it("returns undefined for unknown key", () => {
    expect(findActionFromPolicyKey("unknown", actions)).toBeUndefined();
  });

  it("returns undefined when actions is undefined", () => {
    expect(findActionFromPolicyKey("access_policy")).toBeUndefined();
  });
});

describe("generateFormRulesFromAction", () => {
  it("returns only policy_key rule when no action", () => {
    const rules = generateFormRulesFromAction(undefined);
    expect(rules).toEqual({
      policy_key: [{ required: true, message: "Request type is required" }],
    });
  });

  describe("identity field rules", () => {
    it("generates required + email rules when email is required", () => {
      const action: PrivacyRequestOption = {
        ...baseAction,
        identity_inputs: { email: "required" },
      };
      const rules = generateFormRulesFromAction(action);
      expect(rules["identity.email"]).toEqual([
        { required: true, message: "Email address is required" },
        { type: "email", message: "Email address must be a valid email" },
      ]);
    });

    it("generates only email format rule when email is optional", () => {
      const action: PrivacyRequestOption = {
        ...baseAction,
        identity_inputs: { email: "optional" },
      };
      const rules = generateFormRulesFromAction(action);
      expect(rules["identity.email"]).toEqual([
        { type: "email", message: "Email address must be a valid email" },
      ]);
    });

    it("generates required + pattern rules when phone is required", () => {
      const action: PrivacyRequestOption = {
        ...baseAction,
        identity_inputs: { phone: "required" },
      };
      const rules = generateFormRulesFromAction(action);
      expect(rules["identity.phone_number"]).toHaveLength(2);
      expect(rules["identity.phone_number"]![0]).toEqual({
        required: true,
        message: "Phone number is required",
      });
    });

    it("generates only pattern rule when phone is optional", () => {
      const action: PrivacyRequestOption = {
        ...baseAction,
        identity_inputs: { phone: "optional" },
      };
      const rules = generateFormRulesFromAction(action);
      expect(rules["identity.phone_number"]).toHaveLength(1);
      expect(rules["identity.phone_number"]![0]).toHaveProperty("pattern");
    });

    it("does not generate identity rules when inputs are null", () => {
      const action: PrivacyRequestOption = {
        ...baseAction,
        identity_inputs: null,
      };
      const rules = generateFormRulesFromAction(action);
      expect(rules["identity.email"]).toBeUndefined();
      expect(rules["identity.phone_number"]).toBeUndefined();
    });
  });

  describe("custom field rules", () => {
    it("generates required rule for a required text field (no field_type)", () => {
      const action: PrivacyRequestOption = {
        ...baseAction,
        custom_privacy_request_fields: {
          required_field: {
            label: "Required field",
            required: true,
          },
        },
      };
      const rules = generateFormRulesFromAction(action);
      expect(
        rules["custom_privacy_request_fields.required_field.value"],
      ).toEqual([{ required: true, message: "Required field is required" }]);
    });

    it("does not generate rule for an optional field", () => {
      const action: PrivacyRequestOption = {
        ...baseAction,
        custom_privacy_request_fields: {
          optional_field: {
            label: "Optional field",
            required: false,
          },
        },
      };
      const rules = generateFormRulesFromAction(action);
      expect(
        rules["custom_privacy_request_fields.optional_field.value"],
      ).toBeUndefined();
    });

    it("does not generate required rule for a hidden required field", () => {
      const action: PrivacyRequestOption = {
        ...baseAction,
        custom_privacy_request_fields: {
          hidden_field: {
            label: "Hidden field",
            required: true,
            hidden: true,
          },
        },
      };
      const rules = generateFormRulesFromAction(action);
      expect(
        rules["custom_privacy_request_fields.hidden_field.value"],
      ).toBeUndefined();
    });

    it("generates rule keyed by field name for required location fields", () => {
      const action: PrivacyRequestOption = {
        ...baseAction,
        custom_privacy_request_fields: {
          user_location: {
            label: "Your location",
            required: true,
            field_type: "location",
          },
        },
      };
      const rules = generateFormRulesFromAction(action);
      expect(rules["user_location"]).toEqual([
        { required: true, message: "Your location is required" },
      ]);
      // Should not also generate a nested value path
      expect(
        rules["custom_privacy_request_fields.user_location.value"],
      ).toBeUndefined();
    });

    it("does not generate rule for optional location fields", () => {
      const action: PrivacyRequestOption = {
        ...baseAction,
        custom_privacy_request_fields: {
          user_location: {
            label: "Your location",
            required: false,
            field_type: "location",
          },
        },
      };
      const rules = generateFormRulesFromAction(action);
      expect(rules["user_location"]).toBeUndefined();
    });

    it("generates rules for select fields the same as text fields", () => {
      const action: PrivacyRequestOption = {
        ...baseAction,
        custom_privacy_request_fields: {
          department: {
            label: "Department",
            required: true,
          },
        },
      };
      const rules = generateFormRulesFromAction(action);
      expect(
        rules["custom_privacy_request_fields.department.value"],
      ).toEqual([{ required: true, message: "Department is required" }]);
    });
  });
});
