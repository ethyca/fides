/**
 * Format a timeframe into a readable string
 * @param timeframe Object with days, hours, minutes or just a number of days
 * @returns Formatted timeframe string
 */
export const formatTimeframe = (
  timeframe:
    | number
    | { days?: number; hours?: number; minutes?: number }
    | null
    | undefined,
): string => {
  // Handle null/undefined cases
  if (!timeframe) {
    return "";
  }

  // Parse the input format
  const days = typeof timeframe === "number" ? timeframe : timeframe.days || 0;
  const hours = typeof timeframe === "number" ? 0 : timeframe.hours || 0;
  const minutes = typeof timeframe === "number" ? 0 : timeframe.minutes || 0;

  // If no time values, return empty string
  if (!days && !hours && !minutes) {
    return "";
  }

  // Format each time unit with proper pluralization
  const parts = [
    days > 0 && `${days} day${days !== 1 ? "s" : ""}`,
    hours > 0 && `${hours} hour${hours !== 1 ? "s" : ""}`,
    minutes > 0 && `${minutes} minute${minutes !== 1 ? "s" : ""}`,
  ].filter(Boolean); // Remove falsy values

  return parts.join(", ");
};

// For backward compatibility
export const calculateTimeframe = formatTimeframe;
