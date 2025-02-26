import { Env, FlagConfig, FlagConfigDefaults, FlagEnvs } from "./types";

/**
 * Configure flags and their environments. Each key of the defaults is the name of the flag. The
 * flag can map to either a single value will apply to every environment, or an object with a key
 * for each environment. For example:
 *
 * ```ts
 * configureFlags({
 *   falseEverywhere: false,
 *   envDependent: {
 *     development: true,
 *     test: true,
 *     production: false,
 *   }
 * })
 * ```
 */
export const configureFlags = <Flags>(
  defaults: FlagConfigDefaults<Flags>,
): FlagConfig<Flags> => {
  const config = {} as FlagConfig<Flags>;

  const flagNames = Object.keys(defaults) as Array<keyof Flags>;

  flagNames.forEach((flagName) => {
    const valueOrEnvs = defaults[flagName];
    if (typeof valueOrEnvs === "object") {
      const envs = valueOrEnvs as FlagEnvs<Flags[typeof flagName]>;
      config[flagName] = envs;
      return;
    }

    const value = valueOrEnvs as Flags[typeof flagName];
    config[flagName] = {
      development: value,
      test: value,
      production: value,
    };
  });

  return config;
};

export const flagsForEnv = <Flags>(
  config: FlagConfig<Flags>,
  env: Env,
): Flags => {
  const flags = {} as Flags;

  const flagNames = Object.keys(config) as Array<keyof Flags>;

  flagNames.forEach((flagName) => {
    flags[flagName] = config[flagName][env];
  });

  return flags;
};
