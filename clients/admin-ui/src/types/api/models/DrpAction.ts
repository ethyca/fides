/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Enum to hold valid DRP actions. For more details, see:
 * https://github.com/consumer-reports-digital-lab/data-rights-protocol#301-supported-rights-actions
 */
export enum DrpAction {
  ACCESS = "access",
  DELETION = "deletion",
  SALE_OPT_OUT = "sale:opt_out",
  SALE_OPT_IN = "sale:opt_in",
  ACCESS_CATEGORIES = "access:categories",
  ACCESS_SPECIFIC = "access:specific",
}
