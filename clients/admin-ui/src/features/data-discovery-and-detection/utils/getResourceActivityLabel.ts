import { ResourceChangeType } from "~/features/data-discovery-and-detection/types/ResourceChangeType";
import findResourceChangeType from "~/features/data-discovery-and-detection/utils/findResourceChangeType";
import { StagedResource } from "~/types/api";

import { ResourceActivityTypeEnum } from "../types/ResourceActivityTypeEnum";

const getResourceActivityLabel = (resource: StagedResource) => {
  const changeType = findResourceChangeType(resource);
  if (changeType === ResourceChangeType.CLASSIFICATION) {
    return ResourceActivityTypeEnum.CLASSIFICATION;
  }
  return ResourceActivityTypeEnum.DATASET;
};
export default getResourceActivityLabel;
