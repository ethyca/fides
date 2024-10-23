/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { CustomReportConfig } from "./CustomReportConfig";
import type { ReportType } from "./ReportType";

export type CustomReportResponse = {
  id: string;
  type: ReportType;
  name: string;
  config: CustomReportConfig;
};
