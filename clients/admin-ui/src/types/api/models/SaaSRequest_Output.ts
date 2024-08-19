/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { AsyncConfig } from "./AsyncConfig";
import type { ClientConfig } from "./ClientConfig";
import type { Header } from "./Header";
import type { HTTPMethod } from "./HTTPMethod";
import type { ParamValue_Output } from "./ParamValue_Output";
import type { QueryParam } from "./QueryParam";
import type { RateLimitConfig_Output } from "./RateLimitConfig_Output";
import type { Strategy } from "./Strategy";

/**
 * A single request with static or dynamic path, headers, query, and body params.
 * Also specifies the names and sources for the param values needed to build the request.
 *
 * Includes optional strategies for postprocessing and pagination.
 */
export type SaaSRequest_Output = {
  request_override?: string | null;
  path?: string | null;
  method?: HTTPMethod | null;
  headers?: Array<Header> | null;
  query_params?: Array<QueryParam> | null;
  body?: string | null;
  param_values?: Array<ParamValue_Output> | null;
  client_config?: ClientConfig | null;
  data_path?: string | null;
  postprocessors?: Array<Strategy> | null;
  pagination?: Strategy | null;
  grouped_inputs?: Array<string> | null;
  ignore_errors?: boolean | Array<number> | null;
  rate_limit_config?: RateLimitConfig_Output | null;
  async_config?: AsyncConfig | null;
  skip_missing_param_values?: boolean | null;
};
