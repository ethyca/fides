export type SecretsFieldError = {
  name: (string | number)[];
  errors: string[];
};

export type ParseSecretsFieldErrorsOptions = {
  /** Field names known to the form. Detail entries for unknown fields are ignored. */
  knownFields: Iterable<string>;
  /**
   * Path prefix prepended to each field name. Defaults to ["secrets"] because
   * the integration forms keep secret fields nested under `secrets.*`. Pass an
   * empty array for forms whose fields are at the top level.
   */
  namePrefix?: (string | number)[];
};

type DetailEntry = {
  loc?: unknown[];
  msg?: unknown;
  type?: unknown;
};

const VALUE_ERROR_PREFIX = "Value error, ";
const ENV_VAR_ADVISORY_REGEX =
  /\s*You may change the validation behavior by setting the environment variable[^]*$/;
const FIELD_NAME_FROM_MSG_REGEX = /for '([^']+)'/;

const cleanMessage = (msg: string): string =>
  msg
    .replace(VALUE_ERROR_PREFIX, "")
    .replace(ENV_VAR_ADVISORY_REGEX, "")
    .replace(/[:\s]+$/, "")
    .trim();

const isDetailEntry = (entry: unknown): entry is DetailEntry =>
  typeof entry === "object" && entry !== null && "msg" in entry;

const findFieldName = (
  entry: DetailEntry,
  knownFields: Set<string>,
): string | undefined => {
  if (Array.isArray(entry.loc) && entry.loc.length > 0) {
    const last = entry.loc[entry.loc.length - 1];
    if (typeof last === "string" && knownFields.has(last)) {
      return last;
    }
  }
  if (typeof entry.msg === "string") {
    const match = entry.msg.match(FIELD_NAME_FROM_MSG_REGEX);
    if (match && knownFields.has(match[1])) {
      return match[1];
    }
  }
  return undefined;
};

/**
 * Convert a 422 response from a secrets PATCH (or any endpoint that returns
 * Pydantic-style detail entries) into per-field errors that can be passed to
 * antd's `form.setFields`. Returns null if no detail entries can be mapped to
 * a known field — the caller should fall back to a toast in that case.
 *
 * Pass either an RTK Query unwrap-thrown error (`error.data.detail`) or the
 * `result.error` of a non-unwrapped mutation. Both shapes are accepted.
 */
export const parseSecretsFieldErrors = (
  error: unknown,
  options: ParseSecretsFieldErrorsOptions,
): SecretsFieldError[] | null => {
  const detail = (error as { data?: { detail?: unknown } })?.data?.detail;
  if (!Array.isArray(detail)) {
    return null;
  }

  const knownFields = new Set(options.knownFields);
  if (knownFields.size === 0) {
    return null;
  }
  const namePrefix = options.namePrefix ?? ["secrets"];
  const fieldMessages = new Map<string, string[]>();

  detail.forEach((entry) => {
    if (!isDetailEntry(entry) || typeof entry.msg !== "string") {
      return;
    }
    const fieldName = findFieldName(entry, knownFields);
    if (!fieldName) {
      return;
    }
    const cleaned = cleanMessage(entry.msg);
    if (!cleaned) {
      return;
    }
    const existing = fieldMessages.get(fieldName) ?? [];
    existing.push(cleaned);
    fieldMessages.set(fieldName, existing);
  });

  if (fieldMessages.size === 0) {
    return null;
  }

  return Array.from(fieldMessages.entries()).map(([fieldName, errors]) => ({
    name: [...namePrefix, fieldName],
    errors,
  }));
};
