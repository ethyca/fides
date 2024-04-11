/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

export type Table = {
  urn: string;
  name: string;
  description?: string;
  modified?: string;
  fields?: Array<string>;
  num_rows?: number;
};
