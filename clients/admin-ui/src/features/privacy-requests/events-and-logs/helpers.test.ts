import { ExecutionLog, ExecutionLogStatus } from "privacy-requests/types";

import { ActionType } from "~/types/api";

import { hasUnresolvedError } from "./helpers";

/*
 * Helper function to create log entries with all required fields
 */
const createTestLog = (
  status: ExecutionLogStatus,
  updated_at: string,
  collection_name: string | null,
): ExecutionLog => ({
  status,
  updated_at,
  collection_name,
  fields_affected: [],
  message: "",
  action_type: ActionType.ACCESS,
});

describe("hasUnresolvedError", () => {
  it("should return false when there are no errors", () => {
    const entries: ExecutionLog[] = [
      createTestLog(ExecutionLogStatus.COMPLETE, "2024-01-01", "collection1"),
      createTestLog(ExecutionLogStatus.COMPLETE, "2024-01-02", null),
    ];
    expect(hasUnresolvedError(entries)).toBe(false);
  });

  it("should detect an error without collection name", () => {
    const entries: ExecutionLog[] = [
      createTestLog(ExecutionLogStatus.ERROR, "2024-01-01", null),
    ];
    expect(hasUnresolvedError(entries)).toBe(true);
  });

  it("should ignore collection errors if there is a later complete status", () => {
    const entries: ExecutionLog[] = [
      createTestLog(ExecutionLogStatus.ERROR, "2024-01-01", "collection1"),
      createTestLog(ExecutionLogStatus.COMPLETE, "2024-01-02", null),
    ];
    expect(hasUnresolvedError(entries)).toBe(false);
  });

  it("should keep collection errors if complete status is earlier", () => {
    const entries: ExecutionLog[] = [
      createTestLog(ExecutionLogStatus.COMPLETE, "2024-01-01", null),
      createTestLog(ExecutionLogStatus.ERROR, "2024-01-02", "collection1"),
    ];
    expect(hasUnresolvedError(entries)).toBe(true);
  });

  it("should use latest entry per collection", () => {
    const entries: ExecutionLog[] = [
      createTestLog(ExecutionLogStatus.ERROR, "2024-01-01", "collection1"),
      createTestLog(ExecutionLogStatus.COMPLETE, "2024-01-02", "collection1"),
    ];
    expect(hasUnresolvedError(entries)).toBe(false);
  });

  it("should handle multiple collections", () => {
    const entries: ExecutionLog[] = [
      createTestLog(ExecutionLogStatus.ERROR, "2024-01-01", "collection1"),
      createTestLog(ExecutionLogStatus.ERROR, "2024-01-02", "collection2"),
      createTestLog(ExecutionLogStatus.COMPLETE, "2024-01-03", "collection1"),
      createTestLog(ExecutionLogStatus.COMPLETE, "2024-01-04", "collection2"),
    ];
    expect(hasUnresolvedError(entries)).toBe(false);
  });

  it("should consider no errors when there is a complete entry without collection", () => {
    const entries: ExecutionLog[] = [
      createTestLog(ExecutionLogStatus.ERROR, "2024-01-01", "collection1"),
      createTestLog(ExecutionLogStatus.ERROR, "2024-01-02", "collection2"),
      createTestLog(ExecutionLogStatus.COMPLETE, "2024-01-03", null),
    ];
    expect(hasUnresolvedError(entries)).toBe(false);
  });

  it("should handle empty entries", () => {
    expect(hasUnresolvedError([])).toBe(false);
  });
});
