/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { System_Output } from "./System_Output";

export type SystemScanHistory = {
  id: number;
  status: string;
  result: Array<System_Output>;
  created_at: string;
  updated_at: string;
};
