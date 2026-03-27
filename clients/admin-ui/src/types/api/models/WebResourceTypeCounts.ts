/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Resource type breakdown for website monitors.
 *
 * Keys match the existing ``WEB_MONITOR_RESOURCE_TYPE_API_MAPPING`` values.
 */
export type WebResourceTypeCounts = {
  cookie?: number;
  browser_request?: number;
  image?: number;
  iframe?: number;
  javascript_tag?: number;
};
