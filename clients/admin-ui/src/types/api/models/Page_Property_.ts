/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Property_Output } from "./Property_Output";

export type Page_Property_ = {
  items: Array<Property_Output>;
  total: number | null;
  page: number | null;
  size: number | null;
  pages?: number | null;
};
