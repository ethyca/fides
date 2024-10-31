/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ReportType } from "./ReportType";

/**
 * Simple schema just containing the basic custom report information.
 */
export type CustomReportResponseMinimal = {
  id: string;
  type: ReportType;
  name: string;
};
