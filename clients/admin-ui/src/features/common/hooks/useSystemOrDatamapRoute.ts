import { useFeatures } from "~/features/common/features";
import { DATAMAP_ROUTE, SYSTEM_ROUTE } from "~/features/common/nav/routes";

/**
 * Often we need to either go to the systems page or the datamap page
 * depending on if this is an open source or plus instance
 */
export const useSystemOrDatamapRoute = () => {
  const features = useFeatures();

  const systemOrDatamapRoute = features.plus ? DATAMAP_ROUTE : SYSTEM_ROUTE;

  return { systemOrDatamapRoute };
};
