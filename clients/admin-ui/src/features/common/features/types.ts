/**
 * Flags can only hold primitive values.
 */
export type FlagValue = boolean | string | number;

/**
 * These are the environments that can be targeted. See the README for more info.
 */
export type Env = typeof process.env.NEXT_PUBLIC_APP_ENV;

export type FlagEnvs<Value> = {
  development: Value;
  test: Value;
  production: Value;
  description?: string;
  /**
   * If true, this flag will not show up in the UI as a toggle
   */
  userCannotModify?: boolean;
  /**
   * Array of environments where this flag should be hidden from the UI
   */
  hideFrom?: Env[];
};

/**
 * The format of the `flags.json` file: an object mapping flag names to the values per environment,
 * or a single value that applies everywhere.
 *
 * @example
 * {
 *   falseEverywhere: false,
 *   envDependent: {
 *     development: true,
 *     test: true,
 *     production: false,
 *     description: "Flag changes per environment."
 *   }
 * }
 */
export type FlagConfigDefaults<Flags> = {
  [Name in keyof Flags]: Flags[Name] | FlagEnvs<Flags[Name]>;
};

/**
 * The type of a resolved configuration, which ensures a value is set for each environment.
 *
 * @example
 * {
 *   falseEverywhere: {
 *     development: false,
 *     test: false,
 *     production: false,
 *   },
 *   envDependent: {
 *     development: true,
 *     test: true,
 *     production: false,
 *     description: "Flag changes per environment."
 *   }
 * }
 */
export type FlagConfig<Flags> = {
  [Name in keyof Flags]: FlagEnvs<Flags[Name]>;
};

/**
 * Utility type for extracting the mapping of flag names to flag values for a single environment.
 *
 * @example
 * const flagConfig = {
 *   falseEverywhere: {
 *     development: false,
 *     test: false,
 *     production: false,
 *   },
 *   envDependent: {
 *     development: true,
 *     test: true,
 *     production: false,
 *   },
 * };
 * const flags: FlagsFor<typeof flagConfig> = {
 *   falseEverywhere: false,
 *   envDependent: true,
 * };
 */
export type FlagsFor<FC> = FC extends FlagConfig<infer F> ? F : never;

/**
 * Utility type for getting the names of all flags.
 */
export type NamesFor<FC> = FC extends FlagConfig<infer F> ? keyof F : never;

/**
 * Utility type for getting the value type for a flag.
 */
export type ValueFor<FC, FN> = FN extends keyof FlagsFor<FC>
  ? FlagsFor<FC>[FN]
  : never;
