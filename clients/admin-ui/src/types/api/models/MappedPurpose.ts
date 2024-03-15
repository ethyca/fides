/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Extension of the base GVL purpose model to include properties related to fideslang mappings.
 *
 * This is separated from the base GVL purpose model to keep that model a "pristine" representation
 * of GVL source data.
 */
export type MappedPurpose = {
  /**
   * Official GVL purpose ID. Used for linking with other records, e.g. vendors, cookies, etc.
   */
  id: number;
  /**
   * Name of the GVL purpose.
   */
  name: string;
  /**
   * Description of the GVL purpose.
   */
  description: string;
  /**
   * Illustrative examples of the purpose.
   */
  illustrations: Array<string>;
  /**
   * The fideslang default taxonomy data uses that are associated with the purpose.
   */
  data_uses: Array<string>;
};
