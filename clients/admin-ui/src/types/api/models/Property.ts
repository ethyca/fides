/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import { PropertyType } from "./PropertyTypes";

export type Property = {
  key: string;
  name: string;
  type: PropertyType;
  experiences?: Array<string>;
};
