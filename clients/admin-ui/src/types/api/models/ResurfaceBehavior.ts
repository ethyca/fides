/**
 * ResurfaceBehavior
 *
 * Resurface behavior options - controls when to re-show the banner/modal.
 * Used to configure whether the experience resurfaces after rejection or dismissal.
 *
 * Note: This enum is defined in fidesplus and may not be in the base OpenAPI spec.
 */
export enum ResurfaceBehavior {
  REJECT = "reject",
  DISMISS = "dismiss",
}
