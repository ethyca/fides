/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { CustomReportConfig } from "./CustomReportConfig";
import type { ReportType } from "./ReportType";

export type CustomReportCreate = {
  name: string;
  type: ReportType;
  config: CustomReportConfig;
};
