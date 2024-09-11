import { ResourceChangeType } from "~/features/data-discovery-and-detection/types/ResourceChangeType";
import { DiffStatus, StagedResource } from "~/types/api";

const findResourceChangeType = (resource: StagedResource) => {
  if (resource.diff_status === DiffStatus.ADDITION) {
    return ResourceChangeType.ADDITION;
  }
  if (resource.diff_status === DiffStatus.REMOVAL) {
    return ResourceChangeType.REMOVAL;
  }

  if (
    resource.diff_status === DiffStatus.CLASSIFYING ||
    resource.diff_status === DiffStatus.CLASSIFICATION_QUEUED
  ) {
    return ResourceChangeType.IN_PROGRESS;
  }

  if (
    resource.diff_status === DiffStatus.CLASSIFICATION_ADDITION ||
    resource.diff_status === DiffStatus.CLASSIFICATION_UPDATE
  ) {
    return ResourceChangeType.CLASSIFICATION;
  }
  if (!resource.child_diff_statuses) {
    return ResourceChangeType.NONE;
  }

  if (
    resource.child_diff_statuses[DiffStatus.CLASSIFYING] ||
    resource.child_diff_statuses[DiffStatus.CLASSIFICATION_QUEUED]
  ) {
    return ResourceChangeType.IN_PROGRESS;
  }

  if (
    resource.child_diff_statuses[DiffStatus.CLASSIFICATION_ADDITION] ||
    resource.child_diff_statuses[DiffStatus.CLASSIFICATION_UPDATE]
  ) {
    return ResourceChangeType.CLASSIFICATION;
  }

  if (
    resource.child_diff_statuses[DiffStatus.ADDITION] ||
    resource.child_diff_statuses[DiffStatus.REMOVAL]
  ) {
    return ResourceChangeType.CHANGE;
  }

  if (resource.diff_status === DiffStatus.MONITORED) {
    return ResourceChangeType.MONITORED;
  }
  if (resource.diff_status === DiffStatus.MUTED) {
    return ResourceChangeType.MUTED;
  }

  return ResourceChangeType.NONE;
};

export default findResourceChangeType;
