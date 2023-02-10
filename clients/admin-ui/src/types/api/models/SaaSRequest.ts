/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ClientConfig } from "./ClientConfig";
import type { Header } from "./Header";
import type { HTTPMethod } from "./HTTPMethod";
import type { ParamValue } from "./ParamValue";
import type { QueryParam } from "./QueryParam";
import type { RateLimitConfig } from "./RateLimitConfig";
import type { Strategy } from "./Strategy";

/**
 * A single request with static or dynamic path, headers, query, and body params.
 * Also specifies the names and sources for the param values needed to build the request.
 *
 * Includes optional strategies for postprocessing and pagination.
 */
export type SaaSRequest = {
  request_override?: string;
  path?: string;
  method?: HTTPMethod;
  headers?: Array<Header>;
  query_params?: Array<QueryParam>;
  body?: string;
  param_values?: Array<ParamValue>;
  client_config?: ClientConfig;
  data_path?: string;
  postprocessors?: Array<Strategy>;
  pagination?: Strategy;
  grouped_inputs?: Array<string>;
  ignore_errors?: boolean;
  rate_limit_config?: RateLimitConfig;
  skip_missing_param_values?: boolean;
};
