import {
  ConsentMethod,
  FidesInitOptions,
  NoticeOverrides,
  NoticeOverrideValue,
} from "./consent-types";

export const raise = (message: string) => {
  throw new Error(message);
};

/**
 * Extracts the id value of each object in the list and returns a list
 * of IDs, either strings or numbers based on the IDs' type.
 */
export const extractIds = <T extends { id: string | number }[]>(
  modelList?: T,
): any[] => {
  if (!modelList) {
    return [];
  }
  return modelList.map((model) => model.id);
};

export const isGlobalConsentOverride = (
  value: unknown,
): value is ConsentMethod.ACCEPT | ConsentMethod.REJECT =>
  value === ConsentMethod.ACCEPT || value === ConsentMethod.REJECT;

export const isValidNoticeOverrideValue = (
  value: unknown,
): value is NoticeOverrideValue =>
  typeof value === "number" && value >= 1 && value <= 4;

export const isNoticeOverrides = (value: unknown): value is NoticeOverrides => {
  if (!value || typeof value !== "object") {
    return false;
  }
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  return Object.entries(value).every(([_, val]) =>
    isValidNoticeOverrideValue(val),
  );
};

export const hasConsentOverride = (options: FidesInitOptions) => {
  const override = options.fidesConsentOverride;
  return isGlobalConsentOverride(override) || isNoticeOverrides(override);
};

export const getConsentValueFromOverride = (
  value: NoticeOverrideValue,
): boolean | undefined => {
  switch (value) {
    case NoticeOverrideValue.ACCEPT:
    case NoticeOverrideValue.ACCEPT_DISABLED:
      return true;
    case NoticeOverrideValue.REJECT:
    case NoticeOverrideValue.REJECT_DISABLED:
      return false;
    default:
      return undefined;
  }
};

export const isOverrideDisabled = (value: NoticeOverrideValue): boolean =>
  value === NoticeOverrideValue.ACCEPT_DISABLED ||
  value === NoticeOverrideValue.REJECT_DISABLED;

export const parseNoticeOverrideString = (
  value: string,
): Record<string, number> | null => {
  try {
    // Handle empty or invalid input
    if (!value || !value.startsWith("{") || !value.endsWith("}")) {
      return null;
    }

    // Remove brackets and whitespace
    const content = value.slice(1, -1).trim();
    if (!content) {
      return null;
    }

    // Split into key-value pairs and parse
    const result: Record<string, number> = {};
    content.split(",").forEach((pair) => {
      const [key, val] = pair.split(":").map((s) => s.trim());
      const numVal = parseInt(val, 10);
      if (key && !Number.isNaN(numVal)) {
        result[key] = numVal;
      }
    });

    return Object.keys(result).length > 0 ? result : null;
  } catch {
    return null;
  }
};
