/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ClientConfig } from "./ClientConfig";
import type { ConnectorParam } from "./ConnectorParam";
import type { ConsentRequestMap_Input } from "./ConsentRequestMap_Input";
import type { Endpoint_Input } from "./Endpoint_Input";
import type { ExternalDatasetReference } from "./ExternalDatasetReference";
import type { RateLimitConfig_Input } from "./RateLimitConfig_Input";
import type { SaaSRequest_Input } from "./SaaSRequest_Input";

/**
 * Used to store endpoint and param configurations for a SaaS connector.
 * This is done to separate the details of how to make the API calls
 * from the data provided by a given API collection.
 *
 * The required fields for the config are converted into a Dataset which is
 * merged with the standard Fidesops Dataset to provide a complete set of dependencies
 * for the graph traversal.
 */
export type SaaSConfig_Input = {
  fides_key: string;
  name: string;
  type: string;
  description: string;
  version: string;
  replaceable?: boolean;
  connector_params: Array<ConnectorParam>;
  external_references?: Array<ExternalDatasetReference> | null;
  client_config: ClientConfig;
  endpoints: Array<Endpoint_Input>;
  test_request: SaaSRequest_Input;
  data_protection_request?: SaaSRequest_Input | null;
  rate_limit_config?: RateLimitConfig_Input | null;
  consent_requests?: ConsentRequestMap_Input | null;
  user_guide?: string | null;
};
