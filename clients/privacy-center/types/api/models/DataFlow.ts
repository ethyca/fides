/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * The DataFlow resource model.
 *
 * Describes a resource model with which a given System resource communicates.
 */
export type DataFlow = {
  /**
   * Identifies the System or Dataset resource with which the communication occurs. May also be 'user', to represent communication with the user(s) of a System.
   */
  fides_key: string;
  /**
   * Specifies the resource model class for which the `fides_key` applies. May be any of dataset, system, user.
   */
  type: string;
  /**
   * An array of data categories describing the data in transit.
   */
  data_categories?: Array<string> | null;
};
