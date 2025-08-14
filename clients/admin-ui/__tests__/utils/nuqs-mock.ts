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

const setCalls: Array<Record<string, any> | null> = [];
let currentState: Record<string, any> = {};

const parseFactory = (defaultValue: unknown) => ({
  withDefault: (value: unknown) => ({ default: value ?? defaultValue }),
});

const helpers = {
  reset: (initial: Record<string, any> = {}) => {
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

  useQueryStates: (parsers: Record<string, any>) => {
    const setQueryState = (updates: Record<string, any> | null) => {
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
        } else {
          // eslint-disable-next-line no-param-reassign
          acc[key] = currentValue;
        }
        return acc;
      },
      {} as Record<string, any>,
    );

    return [stateWithDefaults, setQueryState] as const;
  },

  nuqsTestHelpers: helpers,
};

// Type definitions for test helpers
export type NuqsTestHelpers = {
  reset: (initial?: Record<string, any>) => void;
  getSetCalls: () => Array<Record<string, any> | null>;
  getState: () => Record<string, any>;
};
