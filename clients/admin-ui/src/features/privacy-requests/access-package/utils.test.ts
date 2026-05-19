import { RedactionType } from "~/types/api";

import { AccessPackageEntry } from "./types";
import {
  entryToRedaction,
  redactionKey,
  renderValue,
  rowKeyFor,
} from "./utils";

describe("redactionKey", () => {
  it("encodes the three parts as a JSON array", () => {
    expect(redactionKey("postgres_db:customers", 0, "email")).toBe(
      '["postgres_db:customers",0,"email"]',
    );
  });

  it("produces the same key for null and undefined field_path", () => {
    expect(redactionKey("s", 1, null)).toBe(redactionKey("s", 1, undefined));
  });

  it("distinguishes null field_path from empty-string field_path", () => {
    expect(redactionKey("s", 1, null)).not.toBe(redactionKey("s", 1, ""));
  });

  it("does not collide on sources that contain '::'", () => {
    expect(redactionKey("a::b", 1, "x")).not.toBe(
      redactionKey("a", 1, "b::1::x"),
    );
  });
});

describe("rowKeyFor", () => {
  it("delegates to redactionKey using entry fields", () => {
    const entry: AccessPackageEntry = {
      source: "postgres_db:customers",
      record_index: 2,
      field_path: "email",
      redacted: false,
    };
    expect(rowKeyFor(entry)).toBe(
      redactionKey(entry.source, entry.record_index, entry.field_path),
    );
  });
});

describe("entryToRedaction", () => {
  it("emits a REDACT-type redaction copying source/index/field", () => {
    const entry: AccessPackageEntry = {
      source: "postgres_db:customers",
      record_index: 3,
      field_path: "phone",
      value: "+1-555-0100",
      redacted: false,
    };
    expect(entryToRedaction(entry)).toEqual({
      source: "postgres_db:customers",
      record_index: 3,
      field_path: "phone",
      type: RedactionType.REDACT,
    });
  });

  it("does not include the entry's value or redacted flags", () => {
    const entry: AccessPackageEntry = {
      source: "s",
      record_index: 0,
      field_path: "f",
      value: { sensitive: true },
      redacted: true,
    };
    const result = entryToRedaction(entry);
    expect(result).not.toHaveProperty("value");
    expect(result).not.toHaveProperty("redacted");
  });
});

describe("renderValue", () => {
  it("returns an empty string for null", () => {
    expect(renderValue(null)).toBe("");
  });

  it("returns an empty string for undefined", () => {
    expect(renderValue(undefined)).toBe("");
  });

  it("returns the original string unmodified", () => {
    expect(renderValue("hello")).toBe("hello");
  });

  it("preserves whitespace and special characters in strings", () => {
    expect(renderValue("  trailing  ")).toBe("  trailing  ");
    expect(renderValue("a\tb\nc")).toBe("a\tb\nc");
  });

  it("JSON-stringifies numbers and booleans", () => {
    expect(renderValue(42)).toBe("42");
    expect(renderValue(true)).toBe("true");
    expect(renderValue(false)).toBe("false");
  });

  it("JSON-stringifies arrays and objects", () => {
    expect(renderValue([1, 2, 3])).toBe("[1,2,3]");
    expect(renderValue({ a: 1 })).toBe('{"a":1}');
  });

  it("falls back to String() if JSON.stringify throws", () => {
    const circular: Record<string, unknown> = {};
    circular.self = circular;
    expect(() => renderValue(circular)).not.toThrow();
    expect(typeof renderValue(circular)).toBe("string");
  });
});
