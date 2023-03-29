import { configureZones, resolveZone } from "~/features/common/zones";

export const ZONE_CONFIG = configureZones({
  development: {
    host: "localhost:3000",
  },

  zones: [
    {
      basePath: "/plus",
      development: {
        host: "localhost:4000",
      },
    },
  ],
});

export const resolveLink = ({
  href,
  basePath,
}: {
  href: string;
  basePath: string;
}) =>
  resolveZone({
    config: ZONE_CONFIG,
    href,
    basePath,
  });

export const resolveZoneLink = ({
  href,
  router,
  exact = false,
}: {
  href: string;
  router: {
    basePath: string;
    pathname: string;
  };
  exact?: boolean;
}) => {
  // Next's router returns an empty string for the root base path, even the documentation refers the
  // root base path as "/".
  const basePath = router.basePath || "/";

  const zoneLink = resolveLink({
    href,
    basePath,
  });

  // To be active, a link has to be in the same zone (same base path) and its path on that zone must
  // match the current path (either exactly or as as a prefix).
  const isActive =
    basePath === zoneLink.basePath &&
    (exact
      ? router.pathname === zoneLink.href
      : router.pathname.startsWith(zoneLink.href));

  const isCurrentZone = zoneLink.basePath === basePath;

  return {
    ...zoneLink,
    isActive,
    isCurrentZone,
  };
};
