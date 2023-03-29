import { DATAMAP_ROUTE, SYSTEM_ROUTE } from "@fidesui/components";

import { useFeatures } from "~/features/common/features";
import { resolveLink } from "~/features/common/nav/zone-config";

export const useInterzoneNav = () => {
  const features = useFeatures();

  const datamapRoute = resolveLink({
    href: DATAMAP_ROUTE,
    basePath: "/",
  });

  /**
   * Often we need to either go to the systems page or the datamap page
   * depending on if this is an open source or plus instance
   */
  const systemOrDatamapRoute = features.plus ? datamapRoute.href : SYSTEM_ROUTE;

  return { systemOrDatamapRoute };
};
