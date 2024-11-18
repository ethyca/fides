import { ExecutionLogStatus } from "privacy-requests/types";

import { hasUnresolvedError } from "./helpers";

describe("hasUnresolvedError", () => {
  it("should return false when there are no errors", () => {
    const entries = [
      {
        status: ExecutionLogStatus.COMPLETE,
        updated_at: "2024-01-01",
        collection_name: "collection1",
      },
      {
        status: ExecutionLogStatus.COMPLETE,
        updated_at: "2024-01-02",
        collection_name: null,
      },
    ];
    expect(hasUnresolvedError(entries)).toBe(false);
  });

  it("should detect an error without collection name", () => {
    const entries = [
      {
        status: ExecutionLogStatus.ERROR,
        updated_at: "2024-01-01",
        collection_name: null,
      },
    ];
    expect(hasUnresolvedError(entries)).toBe(true);
  });

  it("should ignore collection errors if there is a later complete status", () => {
    const entries = [
      {
        status: ExecutionLogStatus.ERROR,
        updated_at: "2024-01-01",
        collection_name: "collection1",
      },
      {
        status: ExecutionLogStatus.COMPLETE,
        updated_at: "2024-01-02",
        collection_name: null,
      },
    ];
    expect(hasUnresolvedError(entries)).toBe(false);
  });

  it("should keep collection errors if complete status is earlier", () => {
    const entries = [
      {
        status: ExecutionLogStatus.COMPLETE,
        updated_at: "2024-01-01",
        collection_name: null,
      },
      {
        status: ExecutionLogStatus.ERROR,
        updated_at: "2024-01-02",
        collection_name: "collection1",
      },
    ];
    expect(hasUnresolvedError(entries)).toBe(true);
  });

  it("should use latest entry per collection", () => {
    const entries = [
      {
        status: ExecutionLogStatus.ERROR,
        updated_at: "2024-01-01",
        collection_name: "collection1",
      },
      {
        status: ExecutionLogStatus.COMPLETE,
        updated_at: "2024-01-02",
        collection_name: "collection1",
      },
    ];
    expect(hasUnresolvedError(entries)).toBe(false);
  });

  it("should handle multiple collections", () => {
    const entries = [
      {
        status: ExecutionLogStatus.ERROR,
        updated_at: "2024-01-01",
        collection_name: "collection1",
      },
      {
        status: ExecutionLogStatus.ERROR,
        updated_at: "2024-01-02",
        collection_name: "collection2",
      },
      {
        status: ExecutionLogStatus.COMPLETE,
        updated_at: "2024-01-03",
        collection_name: "collection1",
      },
      {
        status: ExecutionLogStatus.COMPLETE,
        updated_at: "2024-01-04",
        collection_name: "collection2",
      },
    ];
    expect(hasUnresolvedError(entries)).toBe(false);
  });

  it("should consider no errors when there is a complete entry without collection", () => {
    const entries = [
      {
        status: ExecutionLogStatus.ERROR,
        updated_at: "2024-01-01",
        collection_name: "collection1",
      },
      {
        status: ExecutionLogStatus.ERROR,
        updated_at: "2024-01-02",
        collection_name: "collection2",
      },
      {
        status: ExecutionLogStatus.COMPLETE,
        updated_at: "2024-01-03",
        collection_name: null,
      },
    ];
    expect(hasUnresolvedError(entries)).toBe(false);
  });

  it("should handle empty entries", () => {
    expect(hasUnresolvedError([])).toBe(false);
  });
});
