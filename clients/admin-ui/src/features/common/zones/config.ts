import { RootConfig } from "./types";

/**
 * Create a configuration with the required types and defaults.
 */
export const configureZones = (config: Partial<RootConfig>): RootConfig => ({
  zones: [],
  ...config,
  basePath: "/",
});

/**
 * Resolve a link path relative to the configured zones.
 *
 * Links within the current zone have their leading base path stripped off so that they can be
 * routed with NextLink (which always routes relative the current zone).
 *
 * Zones are resolved according to their order in the `zones` array, with the first prefix match
 * taking precedence. The root "/" base path is used as the default, meaning an `href` in the root
 * zone will be returned unmodified.
 *
 * In development this also allows us to link to the other locally-hosted client, as configured by
 * the `development` options in a ZoneConfig.
 */
export const resolveZone = ({
  config,
  href,
  basePath,
}: {
  config: RootConfig;
  href: string;
  basePath: string;
}): {
  href: string;
  basePath: string;
} => {
  /* In Cypress, navigating to a URL that is outside of the application will throw an error
   * Instead, we force keeping navigation within the zone for the purpose of avoiding errors
   */
  if (window.Cypress) {
    return { href, basePath };
  }
  const zoneConfig =
    (config.zones ?? []).find((zone) => href.startsWith(zone.basePath)) ??
    config;

  if (zoneConfig.basePath === basePath) {
    const hrefInZone = href.replace(basePath, "/").replace("//", "/");
    return {
      basePath,
      href: hrefInZone,
    };
  }

  if (process.env.NODE_ENV === "development" && zoneConfig.development) {
    const externalZoneUrl = new URL(window.location.href);
    externalZoneUrl.pathname = href;
    externalZoneUrl.host = zoneConfig.development.host;

    return {
      basePath: zoneConfig.basePath,
      href: externalZoneUrl.href,
    };
  }

  return {
    basePath: zoneConfig.basePath,
    href,
  };
};
