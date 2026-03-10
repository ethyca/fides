import { PrivacyRequestFieldDefinition } from "../types";
import {
  formatFieldDisplay,
  formatFieldLabel,
  getCategoryFromFieldPath,
  groupFieldsByCategory,
} from "../utils";

describe("configure-tasks utils", () => {
  describe("formatFieldLabel", () => {
    it("should format simple field names in sentence case", () => {
      expect(formatFieldLabel("privacy_request.email")).toBe("Email");
      expect(formatFieldLabel("privacy_request.source")).toBe("Source");
    });

    it("should format multi-word field names in sentence case", () => {
      expect(formatFieldLabel("privacy_request.policy.has_access_rule")).toBe(
        "Has access rule",
      );
      expect(formatFieldLabel("privacy_request.identity.phone_number")).toBe(
        "Phone number",
      );
      expect(formatFieldLabel("privacy_request.created_at")).toBe("Created at");
    });

    it("should format fields with many underscores", () => {
      expect(formatFieldLabel("privacy_request.policy.rule_action_types")).toBe(
        "Rule action types",
      );
    });
  });

  describe("getCategoryFromFieldPath", () => {
    it("should return mapped category for top-level fields", () => {
      expect(getCategoryFromFieldPath("privacy_request.created_at")).toBe(
        "Privacy request",
      );
      expect(getCategoryFromFieldPath("privacy_request.source")).toBe(
        "Privacy request",
      );
    });

    it("should return mapped category for nested fields", () => {
      expect(getCategoryFromFieldPath("privacy_request.identity.email")).toBe(
        "Identity",
      );
      expect(getCategoryFromFieldPath("privacy_request.policy.name")).toBe(
        "Policy",
      );
      expect(getCategoryFromFieldPath("privacy_request.location")).toBe(
        "Privacy request",
      );
    });

    it("should return raw category name as fallback for unmapped categories", () => {
      expect(
        getCategoryFromFieldPath("privacy_request.unknown_category.field"),
      ).toBe("unknown_category");
    });
  });

  describe("formatFieldDisplay", () => {
    it("should format dataset fields by returning last segment", () => {
      expect(formatFieldDisplay("dataset:collection:field")).toBe("field");
      expect(formatFieldDisplay("my_dataset:users:email")).toBe("email");
    });

    it("should format privacy request nested fields with category", () => {
      expect(formatFieldDisplay("privacy_request.policy.name")).toBe(
        "Policy: Name",
      );
      expect(formatFieldDisplay("privacy_request.identity.email")).toBe(
        "Identity: Email",
      );
      expect(formatFieldDisplay("privacy_request.policy.has_access_rule")).toBe(
        "Policy: Has access rule",
      );
    });

    it("should format privacy request top-level fields without category", () => {
      expect(formatFieldDisplay("privacy_request.created_at")).toBe(
        "Created at",
      );
      expect(formatFieldDisplay("privacy_request.source")).toBe("Source");
    });

    it("should return original string for unknown formats", () => {
      expect(formatFieldDisplay("some.random.string")).toBe(
        "some.random.string",
      );
    });
  });

  describe("groupFieldsByCategory", () => {
    const mockFields: PrivacyRequestFieldDefinition[] = [
      {
        field_path: "privacy_request.created_at",
        field_type: "string",
        description: "Created at",
        is_convenience_field: false,
      },
      {
        field_path: "privacy_request.identity.email",
        field_type: "string",
        description: "Email",
        is_convenience_field: false,
      },
      {
        field_path: "privacy_request.identity.phone_number",
        field_type: "string",
        description: "Phone",
        is_convenience_field: false,
      },
      {
        field_path: "privacy_request.policy.name",
        field_type: "string",
        description: "Policy name",
        is_convenience_field: false,
      },
    ];

    it("should group fields by category", () => {
      const result = groupFieldsByCategory(mockFields);

      expect(result).toHaveLength(3);
      expect(result.map((g) => g.label)).toContain("Privacy request");
      expect(result.map((g) => g.label)).toContain("Identity");
      expect(result.map((g) => g.label)).toContain("Policy");
    });

    it("should sort options within each category alphabetically", () => {
      const result = groupFieldsByCategory(mockFields);

      const identityGroup = result.find((g) => g.label === "Identity");
      expect(identityGroup?.options[0].label).toBe("Email");
      expect(identityGroup?.options[1].label).toBe("Phone number");
    });

    it("should format field labels correctly", () => {
      const result = groupFieldsByCategory(mockFields);

      const policyGroup = result.find((g) => g.label === "Policy");
      expect(policyGroup?.options[0].label).toBe("Name");
      expect(policyGroup?.options[0].value).toBe("privacy_request.policy.name");
    });

    it("should handle empty array", () => {
      const result = groupFieldsByCategory([]);
      expect(result).toEqual([]);
    });
  });
});
