import { DiffStatus, StagedResource } from "~/types/api";
import { ResourceActivityTypeEnum } from "../types/ResourceActivityTypeEnum";

const findActivityType = (resource: StagedResource) => {
  if (
    resource.diff_status === DiffStatus.ADDITION ||
    resource.diff_status === DiffStatus.REMOVAL
  ) {
    return ResourceActivityTypeEnum.DATASET;
  }

  return ResourceActivityTypeEnum.CLASSIFICATION;
};
export default findActivityType;
