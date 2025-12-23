import { PrivacyRequestOption, PrivacyRequestResponse } from "~/types/api";

import {
  extractUniqueCustomFields,
  filterNullCustomFields,
  getCustomFields,
  getOtherIdentities,
  getPrimaryIdentity,
} from "./utils";

// Mock nuqs before importing utils since it's ESM-only and incompatible with Jest
jest.mock("nuqs", () => ({
  createParser: jest.fn(() => ({
    parse: jest.fn(),
    serialize: jest.fn(),
    withOptions: jest.fn(function withOptions() {
      return this;
    }),
  })),
}));

describe("getPrimaryIdentity", () => {
  it("should return email as primary identity when present", () => {
    const identity: PrivacyRequestResponse["identity"] = {
      email: { label: "Email", value: "user@example.com" },
      phone_number: { label: "Phone", value: "+1234567890" },
    };

    const result = getPrimaryIdentity(identity);

    expect(result).toEqual({
      key: "email",
      label: "Email",
      value: "user@example.com",
    });
  });

  it("should return phone_number as primary when email is missing", () => {
    const identity: PrivacyRequestResponse["identity"] = {
      phone_number: { label: "Phone", value: "+1234567890" },
      custom_id: { label: "Custom ID", value: "12345" },
    };

    const result = getPrimaryIdentity(identity);

    expect(result).toEqual({
      key: "phone_number",
      label: "Phone",
      value: "+1234567890",
    });
  });

  it("should return phone_number as primary when email doesn't have a value", () => {
    const identity: PrivacyRequestResponse["identity"] = {
      email: { label: "Email", value: "" },
      phone_number: { label: "Phone", value: "+1234567890" },
    };

    const result = getPrimaryIdentity(identity);

    expect(result).toEqual({
      key: "phone_number",
      label: "Phone",
      value: "+1234567890",
    });
  });

  it("should return first identity when email and phone_number are missing", () => {
    const identity: PrivacyRequestResponse["identity"] = {
      custom_id: { label: "Custom ID", value: "12345" },
      username: { label: "Username", value: "john_doe" },
    };

    const result = getPrimaryIdentity(identity);

    expect(result).toEqual({
      key: "custom_id",
      label: "Custom ID",
      value: "12345",
    });
  });
});

describe("getOtherIdentities", () => {
  it("should return identities excluding the primary identity", () => {
    const allIdentities: PrivacyRequestResponse["identity"] = {
      email: { label: "Email", value: "user@example.com" },
      phone_number: { label: "Phone", value: "+1234567890" },
      custom_id: { label: "Custom ID", value: "12345" },
    };
    const primaryIdentity = {
      key: "email",
      label: "Email",
      value: "user@example.com",
    };

    const result = getOtherIdentities(allIdentities, primaryIdentity);

    expect(result).toEqual([
      { key: "phone_number", label: "Phone", value: "+1234567890" },
      { key: "custom_id", label: "Custom ID", value: "12345" },
    ]);
  });

  it("should filter out identities with empty values", () => {
    const allIdentities: PrivacyRequestResponse["identity"] = {
      email: { label: "Email", value: "user@example.com" },
      phone_number: { label: "Phone", value: "" },
      custom_id: { label: "Custom ID", value: "12345" },
    };
    const primaryIdentity = {
      key: "email",
      label: "Email",
      value: "user@example.com",
    };

    const result = getOtherIdentities(allIdentities, primaryIdentity);

    expect(result).toEqual([
      { key: "custom_id", label: "Custom ID", value: "12345" },
    ]);
  });

  it("should return empty array when only primary identity exists", () => {
    const allIdentities: PrivacyRequestResponse["identity"] = {
      email: { label: "Email", value: "user@example.com" },
    };
    const primaryIdentity = {
      key: "email",
      label: "Email",
      value: "user@example.com",
    };

    const result = getOtherIdentities(allIdentities, primaryIdentity);

    expect(result).toEqual([]);
  });
});

describe("getCustomFields", () => {
  it("should return custom fields with key, label, and value", () => {
    const customFields: PrivacyRequestResponse["custom_privacy_request_fields"] =
      {
        department: { label: "Department", value: "Engineering" },
        employee_id: { label: "Employee ID", value: "EMP123" },
      };

    const result = getCustomFields(customFields);

    expect(result).toEqual([
      { key: "department", label: "Department", value: "Engineering" },
      { key: "employee_id", label: "Employee ID", value: "EMP123" },
    ]);
  });

  it("should filter out fields with empty values", () => {
    const customFields: PrivacyRequestResponse["custom_privacy_request_fields"] =
      {
        department: { label: "Department", value: "Engineering" },
        employee_id: { label: "Employee ID", value: "" },
      };

    const result = getCustomFields(customFields);

    expect(result).toEqual([
      { key: "department", label: "Department", value: "Engineering" },
    ]);
  });

  it("should return empty array when customFields is undefined", () => {
    const result = getCustomFields(undefined);

    expect(result).toEqual([]);
  });

  it("should return empty array when customFields is empty object", () => {
    const customFields: PrivacyRequestResponse["custom_privacy_request_fields"] =
      {};

    const result = getCustomFields(customFields);

    expect(result).toEqual([]);
  });

  it("should include custom fields with value 0", () => {
    const customFields: PrivacyRequestResponse["custom_privacy_request_fields"] =
      {
        department: { label: "Department", value: "Engineering" },
        priority: { label: "Priority", value: 0 },
        count: { label: "Count", value: 5 },
      };

    const result = getCustomFields(customFields);

    expect(result).toEqual([
      { key: "department", label: "Department", value: "Engineering" },
      { key: "priority", label: "Priority", value: 0 },
      { key: "count", label: "Count", value: 5 },
    ]);
  });

  it("should include custom fields with empty array value", () => {
    const customFields: PrivacyRequestResponse["custom_privacy_request_fields"] =
      {
        departments: { label: "Departments", value: [] },
      };

    const result = getCustomFields(customFields);

    expect(result).toEqual([
      { key: "departments", label: "Departments", value: [] },
    ]);
  });
});

describe("filterNullCustomFields", () => {
  it("should return null when input is null", () => {
    const result = filterNullCustomFields(null);

    expect(result).toBeNull();
  });

  it("should return null when all values are null", () => {
    const customFields = {
      field1: null,
      field2: null,
    };

    const result = filterNullCustomFields(customFields);

    expect(result).toBeNull();
  });

  it("should filter out null values and keep valid strings", () => {
    const customFields = {
      department: "Engineering",
      location: null,
      team: "Backend",
    };

    const result = filterNullCustomFields(customFields);

    expect(result).toEqual({
      department: "Engineering",
      team: "Backend",
    });
  });

  it("should return all values when none are null", () => {
    const customFields = {
      department: "Engineering",
      team: "Backend",
      location: "San Francisco",
    };

    const result = filterNullCustomFields(customFields);

    expect(result).toEqual({
      department: "Engineering",
      team: "Backend",
      location: "San Francisco",
    });
  });

  it("should return null for empty object", () => {
    const customFields = {};

    const result = filterNullCustomFields(customFields);

    expect(result).toBeNull();
  });
});

describe("extractUniqueCustomFields", () => {
  it("should return empty object when actions is undefined or empty array", () => {
    expect(extractUniqueCustomFields(undefined)).toEqual({});
    expect(extractUniqueCustomFields([])).toEqual({});
  });

  it("should extract custom fields from a single action", () => {
    const actions: PrivacyRequestOption[] = [
      {
        policy_key: "access",
        icon_path: "/icon.svg",
        title: "Access Request",
        description: "Request access",
        identity_inputs: {},
        custom_privacy_request_fields: {
          department: {
            label: "Department",
            // @ts-expect-error - field_type exists in backend but not in auto-generated types yet
            field_type: "text",
            required: false,
          },
          location: {
            label: "Location",
            // @ts-expect-error - field_type exists in backend but not in auto-generated types yet
            field_type: "select",
            options: ["US", "EU"],
          },
        },
      },
    ];

    const result = extractUniqueCustomFields(actions);

    expect(result).toEqual({
      department: {
        label: "Department",
        field_type: "text",
        required: false,
      },
      location: {
        label: "Location",
        field_type: "select",
        options: ["US", "EU"],
      },
    });
  });

  it("should merge custom fields from multiple actions", () => {
    const actions: PrivacyRequestOption[] = [
      {
        policy_key: "access",
        icon_path: "/icon.svg",
        title: "Access Request",
        description: "Request access",
        identity_inputs: {},
        custom_privacy_request_fields: {
          department: {
            label: "Department",
            // @ts-expect-error - field_type exists in backend but not in auto-generated types yet
            field_type: "text",
          },
        },
      },
      {
        policy_key: "erasure",
        icon_path: "/icon.svg",
        title: "Erasure Request",
        description: "Request erasure",
        identity_inputs: {},
        custom_privacy_request_fields: {
          reason: {
            label: "Reason",
            // @ts-expect-error - field_type exists in backend but not in auto-generated types yet
            field_type: "text",
          },
        },
      },
    ];

    const result = extractUniqueCustomFields(actions);

    expect(result).toEqual({
      department: {
        label: "Department",
        field_type: "text",
      },
      reason: {
        label: "Reason",
        field_type: "text",
      },
    });
  });

  it("should use first occurrence when field name appears multiple times", () => {
    const actions: PrivacyRequestOption[] = [
      {
        policy_key: "access",
        icon_path: "/icon.svg",
        title: "Access Request",
        description: "Request access",
        identity_inputs: {},
        custom_privacy_request_fields: {
          department: {
            label: "Department (Access)",
            // @ts-expect-error - field_type exists in backend but not in auto-generated types yet
            field_type: "text",
          },
        },
      },
      {
        policy_key: "erasure",
        icon_path: "/icon.svg",
        title: "Erasure Request",
        description: "Request erasure",
        identity_inputs: {},
        custom_privacy_request_fields: {
          department: {
            label: "Department (Erasure)",
            // @ts-expect-error - field_type exists in backend but not in auto-generated types yet
            field_type: "select",
            options: ["Eng", "Sales"],
          },
        },
      },
    ];

    const result = extractUniqueCustomFields(actions);

    // First occurrence wins
    expect(result).toEqual({
      department: {
        label: "Department (Access)",
        field_type: "text",
      },
    });
  });

  it("should handle actions with no custom fields", () => {
    const actions: PrivacyRequestOption[] = [
      {
        policy_key: "access",
        icon_path: "/icon.svg",
        title: "Access Request",
        description: "Request access",
        identity_inputs: {},
      },
      {
        policy_key: "erasure",
        icon_path: "/icon.svg",
        title: "Erasure Request",
        description: "Request erasure",
        identity_inputs: {},
      },
    ];

    const result = extractUniqueCustomFields(actions);

    expect(result).toEqual({});
  });

  it("should handle mix of actions with and without custom fields", () => {
    const actions: PrivacyRequestOption[] = [
      {
        policy_key: "access",
        icon_path: "/icon.svg",
        title: "Access Request",
        description: "Request access",
        identity_inputs: {},
        custom_privacy_request_fields: {
          department: {
            label: "Department",
            // @ts-expect-error - field_type exists in backend but not in auto-generated types yet
            field_type: "text",
          },
        },
      },
      {
        policy_key: "erasure",
        icon_path: "/icon.svg",
        title: "Erasure Request",
        description: "Request erasure",
        identity_inputs: {},
      },
    ];

    const result = extractUniqueCustomFields(actions);

    expect(result).toEqual({
      department: {
        label: "Department",
        field_type: "text",
      },
    });
  });
});
