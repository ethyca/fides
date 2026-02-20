import { formatMaskingStrategyName } from "./formatMaskingStrategyName";

describe("formatMaskingStrategyName", () => {
  it.each([
    ["hmac", "HMAC"],
    ["aes_encrypt", "AES Encrypt"],
    ["nlp_redact", "NLP Redact"],
    ["random_string_rewrite", "Random String Rewrite"],
    ["null_rewrite", "Null Rewrite"],
    ["hash", "Hash"],
  ])('formats "%s" as "%s"', (input, expected) => {
    expect(formatMaskingStrategyName(input)).toBe(expected);
  });
});
