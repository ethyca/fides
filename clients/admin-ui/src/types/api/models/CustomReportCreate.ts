/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { CustomReportConfig } from "./CustomReportConfig";
import type { ReportType } from "./ReportType";

/**
 * Schema to create a new custom report.
 */
export type CustomReportCreate = {
  name: string;
  type: ReportType;
  config: CustomReportConfig;
};
