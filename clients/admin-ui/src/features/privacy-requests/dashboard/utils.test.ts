import { PrivacyRequestResponse } from "~/types/api";

import {
  getCustomFields,
  getOtherIdentities,
  getPrimaryIdentity,
} from "./utils";

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
        priority: { label: "Priority", value: 0 as any },
        count: { label: "Count", value: 5 as any },
      };

    const result = getCustomFields(customFields);

    expect(result).toEqual([
      { key: "department", label: "Department", value: "Engineering" },
      { key: "priority", label: "Priority", value: 0 },
      { key: "count", label: "Count", value: 5 },
    ]);
  });
});
