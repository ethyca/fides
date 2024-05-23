/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * General shape for swappable strategies (ex: auth, processors, pagination, etc.)
 */
export type Strategy = {
  strategy: string;
  configuration: any;
};
