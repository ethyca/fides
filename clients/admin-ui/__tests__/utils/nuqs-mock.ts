/**
 * Shared mock for nuqs to handle URL state management in tests
 *
 * NOTE: Our code is not modern enough to use the nuqs testing adapter
 * (specifically the ESM module compatibility) so we're using a custom mock
 * for now. Once ESM is more widely supported, we can switch to the nuqs
 * testing adapter.
 *
 * This mock provides:
 * - URL state management that can be controlled in tests
 * - Helper functions to reset state and inspect calls
 * - Parser factories that match nuqs behavior
 */

const setCalls: Array<Record<string, unknown> | null> = [];
let currentState: Record<string, unknown> = {};

const parseFactory = (defaultValue: unknown) => ({
  withDefault: (value: unknown) => ({ default: value ?? defaultValue }),
});

const helpers = {
  reset: (initial: Record<string, unknown> = {}) => {
    currentState = { ...initial };
    setCalls.length = 0;
  },
  getSetCalls: () => setCalls,
  getState: () => currentState,
};

export const nuqsMock = {
  esModule: true,
  parseAsInteger: parseFactory(1),
  parseAsString: parseFactory(""),
  parseAsStringLiteral: () => ({
    withDefault: (value: unknown) => ({ default: value }),
    default: null,
  }),
  parseAsJson: () => ({
    withDefault: (value: unknown) => ({ default: value }),
  }),
  createParser: (config: {
    parse: (value: string) => unknown;
    serialize: (value: unknown) => string;
  }) => ({
    withDefault: (defaultValue: unknown) => ({
      default: defaultValue,
      parse: config.parse,
      serialize: config.serialize,
    }),
  }),

  useQueryStates: (
    parsers: Record<
      string,
      { default?: unknown; parse?: (value: string) => unknown }
    >,
  ) => {
    const setQueryState = (updates: Record<string, unknown> | null) => {
      setCalls.push(updates);
      if (updates && typeof updates === "object") {
        // Handle both approaches: preserve null values (for most tests)
        // but also support filtering them out (for pagination-specific behavior)
        currentState = { ...currentState, ...updates };
      }
    };

    // Return current state values, but fall back to parser defaults when undefined
    const stateWithDefaults = Object.keys(parsers).reduce(
      (acc, key) => {
        const parser = parsers[key];
        const currentValue = currentState[key];

        // If value is undefined, use the parser's default
        if (currentValue === undefined && parser?.default !== undefined) {
          // eslint-disable-next-line no-param-reassign
          acc[key] = parser.default;
        } else if (currentValue !== undefined && parser?.parse) {
          // If parser has a parse function (custom parser), use it to validate
          try {
            const parsedValue = parser.parse(String(currentValue));
            // eslint-disable-next-line no-param-reassign
            acc[key] = parsedValue !== null ? parsedValue : parser.default;
          } catch {
            // If parsing fails, use default
            // eslint-disable-next-line no-param-reassign
            acc[key] = parser.default;
          }
        } else {
          // eslint-disable-next-line no-param-reassign
          acc[key] = currentValue;
        }
        return acc;
      },
      {} as Record<string, unknown>,
    );

    return [stateWithDefaults, setQueryState] as const;
  },

  nuqsTestHelpers: helpers,
};

// Type definitions for test helpers
export type NuqsTestHelpers = {
  reset: (initial?: Record<string, unknown>) => void;
  getSetCalls: () => Array<Record<string, unknown> | null>;
  getState: () => Record<string, unknown>;
};
