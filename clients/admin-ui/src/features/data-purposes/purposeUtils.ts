import { CUSTOM_TAG_COLOR } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";

import type { DataPurpose } from "./data-purpose.slice";

export const DATA_USE_LABELS: Record<string, string> = {
  analytics: "Analytics",
  "marketing.advertising": "Marketing & Advertising",
  "essential.service.security": "Security & Fraud Prevention",
  "essential.service.operations": "Essential Services",
  improve: "Product Improvement",
};

export const formatDataUse = (key: string): string =>
  DATA_USE_LABELS[key] ?? key;

export const DATA_USE_COLORS: Record<string, string> = {
  analytics: palette.FIDESUI_OLIVE,
  "marketing.advertising": palette.FIDESUI_TERRACOTTA,
  "essential.service.security": palette.FIDESUI_MINOS,
  "essential.service.operations": palette.FIDESUI_SANDSTONE,
  improve: palette.FIDESUI_INFO,
};

export const LEGAL_BASIS_LABELS: Record<string, string> = {
  legitimate_interests: "Legitimate interests",
  consent: "Consent",
  contract: "Contract",
};

export const LEGAL_BASIS_TAG_COLORS: Record<string, CUSTOM_TAG_COLOR> = {
  legitimate_interests: CUSTOM_TAG_COLOR.OLIVE,
  consent: CUSTOM_TAG_COLOR.NECTAR,
  contract: CUSTOM_TAG_COLOR.SANDSTONE,
};

export const FEATURE_LABELS: Record<string, string> = {
  linking_devices: "Linking across devices",
  automated_decisions: "Automated decision-making",
  profiling: "Profiling",
};

export const getFeatureLabel = (key: string): string =>
  FEATURE_LABELS[key] ?? key;

export const getCompleteness = (p: DataPurpose): number => {
  const checks = [
    !!p.description,
    !!p.data_use,
    (p.data_categories ?? []).length > 0,
    !!p.data_subject,
    !!p.legal_basis_for_processing,
    p.retention_period !== null && p.retention_period !== undefined,
    !!p.special_category_legal_basis,
    (p.features ?? []).length > 0,
  ];
  return Math.round((checks.filter(Boolean).length / checks.length) * 100);
};

export const getStrokeColor = (percent: number): string => {
  if (percent >= 80) {
    return palette.FIDESUI_SUCCESS;
  }
  if (percent >= 50) {
    return palette.FIDESUI_WARNING;
  }
  return palette.FIDESUI_ERROR;
};

export type ComplianceStatus = "compliant" | "drift" | "unknown";

export interface CategoryDrift {
  status: ComplianceStatus;
  /** Detected categories not in the defined set (scope drift). */
  undeclared: string[];
  /** Defined categories not in the detected set (unused declarations). */
  unused: string[];
}

/**
 * Compare the purpose's human-authored `defined` categories against the
 * classifier's `detected` categories and classify the result.
 *
 * - `unknown` when nothing has been detected yet (no signal).
 * - `drift` when detected includes categories not in the defined set.
 * - `compliant` when detected is a subset of defined.
 *
 * `unused` surfaces defined categories with no detection — a data minimization
 * signal, not a compliance failure.
 */
export const computeCategoryDrift = (
  defined: string[],
  detected: string[],
): CategoryDrift => {
  if (detected.length === 0) {
    return { status: "unknown", undeclared: [], unused: [] };
  }
  const definedSet = new Set(defined);
  const detectedSet = new Set(detected);
  const undeclared = detected.filter((c) => !definedSet.has(c));
  const unused = defined.filter((c) => !detectedSet.has(c));
  return {
    status: undeclared.length > 0 ? "drift" : "compliant",
    undeclared,
    unused,
  };
};
