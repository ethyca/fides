const ACRONYMS = new Set(["aes", "hmac", "nlp"]);

/**
 * Converts a snake_case masking strategy name (e.g. "hmac_hash", "aes_encrypt")
 * into a human-readable label (e.g. "HMAC Hash", "AES Encrypt").
 * Known acronyms are uppercased; other words are title-cased.
 */
export const formatMaskingStrategyName = (name: string): string =>
  name
    .split("_")
    .map((word) =>
      ACRONYMS.has(word)
        ? word.toUpperCase()
        : word.charAt(0).toUpperCase() + word.slice(1),
    )
    .join(" ");
