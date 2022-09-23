/**
 * This template type ensures we always configure routes with leading "/" which is necessary for
 * base path matching.
 */
export type Path = `/${string}`;

export interface ZoneConfig {
  basePath: Path;
  development?: {
    host: string;
  };
}

/**
 * The root config must be for the "/" base path. Routes under more specific base paths are defined
 * under `zones`.
 */
export interface RootConfig extends ZoneConfig {
  basePath: "/";
  zones: ZoneConfig[];
}
