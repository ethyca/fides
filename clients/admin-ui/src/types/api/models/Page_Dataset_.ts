/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Dataset_Output } from "./Dataset_Output";

export type Page_Dataset_ = {
  items: Array<Dataset_Output>;
  total: number | null;
  page: number | null;
  size: number | null;
  pages?: number | null;
};
