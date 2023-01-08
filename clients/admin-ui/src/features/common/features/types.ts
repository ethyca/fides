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
};

export type FlagConfigDefaults<Flags> = {
  [Name in keyof Flags]: Flags[Name] | FlagEnvs<Flags[Name]>;
};

export type FlagConfig<Flags> = {
  [Name in keyof Flags]: FlagEnvs<Flags[Name]>;
};

export type FlagsFor<FC> = FC extends FlagConfig<infer F> ? F : never;

export type NamesFor<FC> = FC extends FlagConfig<infer F> ? keyof F : never;

export type ValueFor<FC, FN> = FN extends keyof FlagsFor<FC>
  ? FlagsFor<FC>[FN]
  : never;
