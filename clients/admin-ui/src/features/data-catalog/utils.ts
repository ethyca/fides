import { DiffStatus, StagedResourceAPIResponse } from "~/types/api";

/** TODO: centralize to a ResourceStatus mapping */
export enum CatalogResourceStatus {
  ATTENTION_REQUIRED = "Attention required",
  CLASSIFIED = "Classified",
  REVIEWED = "Reviewed",
  CLASSIFYING = "Classifying",
  NONE = "None",
}

export const getCatalogResourceStatus = (
  resource: StagedResourceAPIResponse | undefined,
) => {
  if (!resource) {
    return CatalogResourceStatus.REVIEWED;
  }
  const resourceSchemaChanged =
    resource.diff_status === DiffStatus.ADDITION ||
    resource.diff_status === DiffStatus.REMOVAL;
  const resourceChildrenSchemaChanged =
    resource.child_diff_statuses &&
    (resource.child_diff_statuses[DiffStatus.ADDITION] ||
      resource.child_diff_statuses[DiffStatus.REMOVAL]);

  if (resourceSchemaChanged || resourceChildrenSchemaChanged) {
    return CatalogResourceStatus.ATTENTION_REQUIRED;
  }

  const classificationInProgress =
    resource.diff_status === DiffStatus.CLASSIFICATION_QUEUED ||
    resource.diff_status === DiffStatus.CLASSIFYING;
  const childClassificationInProgress =
    resource.child_diff_statuses &&
    (resource.child_diff_statuses[DiffStatus.CLASSIFICATION_QUEUED] ||
      resource.child_diff_statuses[DiffStatus.CLASSIFYING]);

  if (classificationInProgress || childClassificationInProgress) {
    return CatalogResourceStatus.CLASSIFYING;
  }

  const classificationChanged =
    resource.diff_status === DiffStatus.CLASSIFICATION_ADDITION ||
    resource.diff_status === DiffStatus.CLASSIFICATION_UPDATE;
  const childClassificationChanged =
    resource.child_diff_statuses &&
    (resource.child_diff_statuses[DiffStatus.CLASSIFICATION_ADDITION] ||
      resource.child_diff_statuses[DiffStatus.CLASSIFICATION_UPDATE]);

  if (classificationChanged || childClassificationChanged) {
    return CatalogResourceStatus.CLASSIFIED;
  }

  return CatalogResourceStatus.REVIEWED;
};
