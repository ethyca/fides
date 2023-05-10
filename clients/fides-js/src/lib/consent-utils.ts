/**
 * Wrapper around 'console.log' that only logs output when the 'debug' banner
 * option is truthy
 */
type ConsoleLogParameters = Parameters<typeof console.log>;
export const debugLog = (
  enabled: boolean,
  ...args: ConsoleLogParameters
): void => {
  if (enabled) {
    // eslint-disable-next-line no-console
    console.log(...args); // TODO: use console.debug instead?
  }
};
