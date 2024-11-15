import { SystemType } from "~/types/api/models/SystemType";
import { generateIntegrationKey } from "./helpers";

describe("generateIntegrationKey", () => {
  it("removes special characters except allowed ones", () => {
    const result = generateIntegrationKey("test.system!@#$%^&*()", {
      identifier: "test",
      type: SystemType.DATABASE,
    });
    expect(result).toBe("testsystem");
  });

  it("keeps allowed characters (alphanumeric, hyphen, underscore)", () => {
    const result = generateIntegrationKey("test-system_123", {
      identifier: "test",
      type: SystemType.DATABASE,
    });
    expect(result).toBe("test-system_123");
  });

  it("adds identifier if not present", () => {
    const result = generateIntegrationKey("system", {
      identifier: "postgres",
      type: SystemType.DATABASE,
    });
    expect(result).toBe("system_postgres");
  });

  it("does not add identifier if already present", () => {
    const result = generateIntegrationKey("system_postgres", {
      identifier: "postgres",
      type: SystemType.DATABASE,
    });
    expect(result).toBe("system_postgres");
  });

  it("adds API suffix for SaaS type", () => {
    const result = generateIntegrationKey("system", {
      identifier: "salesforce",
      type: SystemType.SAAS,
    });
    expect(result).toBe("system_salesforce_api");
  });
});
