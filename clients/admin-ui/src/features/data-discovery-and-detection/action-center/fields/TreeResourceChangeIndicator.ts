/**
 * Frontend-only enum mapping DiffStatus values to tree change indicators.
 * Not in the backend OpenAPI spec.
 */
export enum TreeResourceChangeIndicator {
  ADDITION = "addition",
  REMOVAL = "removal",
  CLASSIFICATION_ADDITION = "classification_addition",
  CLASSIFICATION_UPDATE = "classification_update",
}
