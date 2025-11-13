/**
 * Constants for GPC conditional text markers
 */
export const GPC_START = "__GPC_START__";
export const GPC_END = "__GPC_END__";
export const NO_GPC_START = "__NO_GPC_START__";
export const NO_GPC_END = "__NO_GPC_END__";

/**
 * Process GPC conditional text blocks in a string.
 *
 * Text wrapped in __GPC_START__...__GPC_END__ will only show when GPC is enabled.
 * Text wrapped in __NO_GPC_START__...__NO_GPC_END__ will only show when GPC is NOT enabled.
 *
 * @param text - The text containing potential GPC conditional markers
 * @param hasGpc - Whether GPC is currently enabled
 * @returns The processed text with appropriate conditional blocks shown/hidden
 *
 * @example
 * // Returns: "Thank you for enabling GPC!"
 * processGpcConditionals(
 *   "We value your privacy. __GPC_START__Thank you for enabling GPC!__GPC_END____NO_GPC_START__Manage your preferences.__NO_GPC_END__",
 *   true
 * );
 */
export const processGpcConditionals = (
  text: string | undefined,
  hasGpc: boolean,
): string => {
  if (!text) {
    return "";
  }

  // Check if text contains any GPC markers
  const hasGpcMarkers =
    text.includes(GPC_START) ||
    text.includes(GPC_END) ||
    text.includes(NO_GPC_START) ||
    text.includes(NO_GPC_END);

  if (!hasGpcMarkers) {
    return text;
  }

  let processed = text;

  if (hasGpc) {
    // Show GPC content, hide NO_GPC content
    processed = processed.replace(
      new RegExp(`${GPC_START}(.*?)${GPC_END}`, "gs"),
      "$1",
    );
    processed = processed.replace(
      new RegExp(`${NO_GPC_START}(.*?)${NO_GPC_END}`, "gs"),
      "",
    );
  } else {
    // Hide GPC content, show NO_GPC content
    processed = processed.replace(
      new RegExp(`${GPC_START}(.*?)${GPC_END}`, "gs"),
      "",
    );
    processed = processed.replace(
      new RegExp(`${NO_GPC_START}(.*?)${NO_GPC_END}`, "gs"),
      "$1",
    );
  }

  // Clean up any extra whitespace that might have been left behind
  processed = processed.replace(/\s{2,}/g, " ").trim();

  return processed;
};
