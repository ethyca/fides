import {
  buildOrderedFields,
  OrderedField,
} from "~/components/modals/privacy-request-modal/buildOrderedFields";
import { CustomConfigField } from "~/types/config";

const textField = (label: string): CustomConfigField => ({
  label,
  field_type: "text",
  required: false,
});

// Helper that flattens a descriptor into a stable string for comparison.
const stringifyField = (f: OrderedField): string => {
  switch (f.kind) {
    case "name":
    case "email":
    case "phone":
      return `${f.kind}:${f.mode}`;
    case "custom-identity":
    case "custom":
      return `${f.kind}:${f.key}`;
    default: {
      const exhaustive: never = f;
      throw new Error(`unhandled: ${JSON.stringify(exhaustive)}`);
    }
  }
};

describe("buildOrderedFields", () => {
  describe("with field_order present", () => {
    it("renders strictly in field_order, interleaving identity and customs", () => {
      const result = buildOrderedFields(
        { name: "optional", email: "required", phone: "optional" },
        {},
        { reason: textField("Reason"), topics: textField("Topics") },
        ["email", "reason", "name", "topics", "phone"],
      );

      expect(result.map((f) => stringifyField(f))).toEqual([
        "email:required",
        "custom:reason",
        "name:optional",
        "custom:topics",
        "phone:optional",
      ]);
    });

    it("places custom identity fields via field_order entries", () => {
      const result = buildOrderedFields(
        { email: "required" },
        { loyalty_id: textField("Loyalty ID") },
        {},
        ["loyalty_id", "email"],
      );

      expect(result.map((f) => stringifyField(f))).toEqual([
        "custom-identity:loyalty_id",
        "email:required",
      ]);
    });

    it("appends configured fields missing from field_order to the end", () => {
      const result = buildOrderedFields(
        { email: "required", phone: "optional" },
        {},
        { reason: textField("Reason") },
        ["reason", "email"], // `phone` configured but not listed
      );

      expect(result.map((f) => stringifyField(f))).toEqual([
        "custom:reason",
        "email:required",
        "phone:optional",
      ]);
    });

    it("ignores unknown keys in field_order without crashing", () => {
      const result = buildOrderedFields(
        { email: "required" },
        {},
        { reason: textField("Reason") },
        ["email", "ghost_field", "reason"],
      );

      expect(result.map((f) => stringifyField(f))).toEqual([
        "email:required",
        "custom:reason",
      ]);
    });

    it("dedupes repeated keys (defensive against stale data)", () => {
      const result = buildOrderedFields(
        { email: "required" },
        {},
        { reason: textField("Reason") },
        ["email", "reason", "email"],
      );

      expect(result.map((f) => stringifyField(f))).toEqual([
        "email:required",
        "custom:reason",
      ]);
    });
  });

  describe("legacy fallback (no field_order)", () => {
    it("renders name → email → phone → custom identities → customs", () => {
      const result = buildOrderedFields(
        { phone: "optional", email: "required", name: "optional" },
        { loyalty_id: textField("Loyalty ID") },
        { reason: textField("Reason"), topics: textField("Topics") },
      );

      expect(result.map((f) => stringifyField(f))).toEqual([
        "name:optional",
        "email:required",
        "phone:optional",
        "custom-identity:loyalty_id",
        "custom:reason",
        "custom:topics",
      ]);
    });

    it("skips identity fields not configured", () => {
      const result = buildOrderedFields(
        { email: "required" },
        {},
        { reason: textField("Reason") },
      );

      expect(result.map((f) => stringifyField(f))).toEqual([
        "email:required",
        "custom:reason",
      ]);
    });

    it("returns an empty array when no fields are configured", () => {
      expect(buildOrderedFields({}, {}, {})).toEqual([]);
    });

    it("treats null / undefined / empty field_order as absent", () => {
      const args = [
        { email: "required" },
        {},
        { reason: textField("Reason") },
      ] as const;
      const expected = ["email:required", "custom:reason"];

      expect(
        buildOrderedFields(...args, null).map((f) => stringifyField(f)),
      ).toEqual(expected);
      expect(
        buildOrderedFields(...args, undefined).map((f) => stringifyField(f)),
      ).toEqual(expected);
      expect(
        buildOrderedFields(...args, []).map((f) => stringifyField(f)),
      ).toEqual(expected);
    });
  });
});
