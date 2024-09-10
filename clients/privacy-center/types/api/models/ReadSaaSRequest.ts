/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { AsyncConfig } from "./AsyncConfig";
import type { ClientConfig } from "./ClientConfig";
import type { Header } from "./Header";
import type { HTTPMethod } from "./HTTPMethod";
import type { ParamValue } from "./ParamValue";
import type { QueryParam } from "./QueryParam";
import type { RateLimitConfig } from "./RateLimitConfig";
import type { Strategy } from "./Strategy";

/**
 * An extension of the base SaaSRequest that allows the inclusion of an output template
 * that is used to format each collection result.
 */
export type ReadSaaSRequest = {
  request_override?: string | null;
  path?: string | null;
  method?: HTTPMethod | null;
  headers?: Array<Header> | null;
  query_params?: Array<QueryParam> | null;
  body?: string | null;
  param_values?: Array<ParamValue> | null;
  client_config?: ClientConfig | null;
  data_path?: string | null;
  postprocessors?: Array<Strategy> | null;
  pagination?: Strategy | null;
  grouped_inputs?: Array<string> | null;
  ignore_errors?: boolean | Array<number> | null;
  rate_limit_config?: RateLimitConfig | null;
  async_config?: AsyncConfig | null;
  skip_missing_param_values?: boolean | null;
  output?: string | null;
};
