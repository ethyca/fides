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
  ignore_errors?: boolean | Array<number>;
  rate_limit_config?: RateLimitConfig;
  async_config?: AsyncConfig;
  skip_missing_param_values?: boolean;
  output?: string;
};
