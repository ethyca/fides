/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import { PropertyType } from "./PropertyType";

export type Property = {
  id: string;
  name: string;
  type: PropertyType;
  experiences: Array<string>;
};
