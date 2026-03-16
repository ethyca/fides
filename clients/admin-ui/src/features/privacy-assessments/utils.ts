import { formatFieldName } from "~/features/common/utils";

import { SOURCE_TYPE_LABELS } from "./constants";
import type { AssessmentTaskResponse, EvidenceItem } from "./types";

export const formatSystems = (task: AssessmentTaskResponse | null): string => {
  if (!task) {
    return "—";
  }

  // Prefer systems array with name fallback to fides_key
  if (task.systems && task.systems.length > 0) {
    return task.systems
      .map((system) => system.name ?? system.fides_key)
      .join(", ");
  }

  // Fall back to system_fides_keys
  if (task.system_fides_keys && task.system_fides_keys.length > 0) {
    return task.system_fides_keys.join(", ");
  }

  return "All systems";
};

export const formatTypes = (
  assessmentTypes: string[],
  namesMap?: Record<string, string>,
): string => {
  if (assessmentTypes.length === 0) {
    return "—";
  }
  return assessmentTypes.map((t) => namesMap?.[t] ?? t).join(", ");
};

export const deduplicateEvidence = (items: EvidenceItem[]): EvidenceItem[] => {
  const seen = new Set<string>();
  return items.filter((item) => {
    const key = `${item.source_type}|${item.source_key}|${item.field_name}|${item.value}`;
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
};

export const filterEvidence = (
  items: EvidenceItem[],
  query: string,
): EvidenceItem[] => {
  if (!query.trim()) {
    return items;
  }
  const lower = query.toLowerCase();
  return items.filter(
    (item) =>
      item.value.toLowerCase().includes(lower) ||
      (SOURCE_TYPE_LABELS[item.source_type] ?? item.source_type)
        .toLowerCase()
        .includes(lower) ||
      formatFieldName(item.field_name).toLowerCase().includes(lower),
  );
};
