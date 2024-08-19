/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ClientConfig } from "./ClientConfig";
import type { ConnectorParam } from "./ConnectorParam";
import type { ConsentRequestMap_Output } from "./ConsentRequestMap_Output";
import type { Endpoint_Output } from "./Endpoint_Output";
import type { ExternalDatasetReference } from "./ExternalDatasetReference";
import type { RateLimitConfig_Output } from "./RateLimitConfig_Output";
import type { SaaSRequest_Output } from "./SaaSRequest_Output";

/**
 * Used to store endpoint and param configurations for a SaaS connector.
 * This is done to separate the details of how to make the API calls
 * from the data provided by a given API collection.
 *
 * The required fields for the config are converted into a Dataset which is
 * merged with the standard Fidesops Dataset to provide a complete set of dependencies
 * for the graph traversal.
 */
export type SaaSConfig_Output = {
  fides_key: string;
  name: string;
  type: string;
  description: string;
  version: string;
  replaceable?: boolean;
  connector_params: Array<ConnectorParam>;
  external_references?: Array<ExternalDatasetReference> | null;
  client_config: ClientConfig;
  endpoints: Array<Endpoint_Output>;
  test_request: SaaSRequest_Output;
  data_protection_request?: SaaSRequest_Output | null;
  rate_limit_config?: RateLimitConfig_Output | null;
  consent_requests?: ConsentRequestMap_Output | null;
  user_guide?: string | null;
};
