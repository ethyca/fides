/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { CustomReportConfig } from "./CustomReportConfig";
import type { ReportType } from "./ReportType";

/**
 * Response containing the basic custom report information along with the actual custom report configuration.
 */
export type CustomReportResponse = {
  id: string;
  type: ReportType;
  name: string;
  config: CustomReportConfig;
};
