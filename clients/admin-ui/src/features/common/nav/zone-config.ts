import { configureZones, resolveZone } from "~/features/common/zones";

export const ZONE_CONFIG = configureZones({
  development: {
    host: "localhost:3000",
  },

  zones: [
    {
      basePath: "/datamap",
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
