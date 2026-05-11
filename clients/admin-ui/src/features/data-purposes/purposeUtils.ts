export const DATA_USE_LABELS: Record<string, string> = {
  analytics: "Analytics",
  "marketing.advertising": "Marketing & Advertising",
  "essential.service.security": "Security & Fraud Prevention",
  "essential.service.operations": "Essential Services",
  improve: "Product Improvement",
};

export const formatDataUse = (key: string): string =>
  DATA_USE_LABELS[key] ?? key;

export type ComplianceStatus = "compliant" | "drift" | "unknown";

export interface CategoryDrift {
  status: ComplianceStatus;
  undeclared: string[];
  unused: string[];
}

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
