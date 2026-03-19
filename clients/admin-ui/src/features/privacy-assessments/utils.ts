import { FIELD_NAME_LABELS, SOURCE_TYPE_LABELS } from "./constants";
import type { AssessmentTaskResponse, EvidenceItem } from "./types";
import { EvidenceType } from "./types";

export const getInitials = (name: string) =>
  name
    .split(/\s+/)
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase();

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

const matchesQuery = (item: EvidenceItem, lower: string): boolean => {
  if (item.type === EvidenceType.TEAM_INPUT) {
    return (
      !!item.value?.toLowerCase().includes(lower) ||
      !!item.data?.channel?.toLowerCase().includes(lower) ||
      !!item.data?.messages.some(
        (msg) =>
          msg.sender.toLowerCase().includes(lower) ||
          msg.text.toLowerCase().includes(lower),
      )
    );
  }
  return (
    !!item.value?.toLowerCase().includes(lower) ||
    !!(
      item.source_type &&
      (SOURCE_TYPE_LABELS[item.source_type] ?? item.source_type)
        .toLowerCase()
        .includes(lower)
    ) ||
    !!(
      item.field_name &&
      (FIELD_NAME_LABELS[item.field_name] ?? item.field_name.replace(/_/g, " "))
        .toLowerCase()
        .includes(lower)
    )
  );
};

export const filterEvidence = (
  items: EvidenceItem[],
  query: string,
): EvidenceItem[] => {
  if (!query.trim()) {
    return items;
  }
  const lower = query.toLowerCase();
  return items.filter((item) => matchesQuery(item, lower));
};
