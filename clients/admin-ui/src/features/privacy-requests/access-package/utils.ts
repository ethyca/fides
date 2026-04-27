import { RedactionType } from "~/types/api";

import { AccessPackageEntry } from "./types";

/**
 * Stable key for a redactable target. Used as the Table rowKey for
 * AccessPackageEntry rows and to compare against existing RedactionEntry
 * items (whose field_path is null for REMOVE_RECORD-type redactions).
 */
export const redactionKey = (
  source: string,
  recordIndex: number,
  fieldPath: string | null | undefined,
) => `${source}::${recordIndex}::${fieldPath ?? ""}`;

export const rowKeyFor = (e: AccessPackageEntry) =>
  redactionKey(e.source, e.record_index, e.field_path);

type RedactRedactionEntry = {
  source: string;
  record_index: number;
  field_path: string;
  type: RedactionType.REDACT;
};

export const entryToRedaction = (
  e: AccessPackageEntry,
): RedactRedactionEntry => ({
  source: e.source,
  record_index: e.record_index,
  field_path: e.field_path,
  type: RedactionType.REDACT,
});

export const renderValue = (value: unknown): string => {
  if (value === null || value === undefined) {
    return "";
  }
  if (typeof value === "string") {
    return value;
  }
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
};
