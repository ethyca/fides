/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

export enum DiffStatus {
  ADDITION = "addition",
  CLASSIFICATION_ADDITION = "classification_addition",
  CLASSIFICATION_UPDATE = "classification_update",
  REVIEWED = "reviewed",
  MONITORED = "monitored",
  REMOVAL = "removal",
  MUTED = "muted",
  CLASSIFICATION_QUEUED = "classification_queued",
  CLASSIFYING = "classifying",
  PROMOTING = "promoting",
  REMOVING = "removing",
  CLASSIFICATION_ERROR = "classification_error",
  PROMOTION_ERROR = "promotion_error",
  REMOVAL_PROMOTION_ERROR = "removal_promotion_error",
}
