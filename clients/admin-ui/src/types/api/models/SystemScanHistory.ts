/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { System } from "./System";

export type SystemScanHistory = {
  id: number;
  status: string;
  result: Array<System>;
  created_at: string;
  updated_at: string;
};
