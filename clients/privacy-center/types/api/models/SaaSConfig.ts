/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ClientConfig } from "./ClientConfig";
import type { ConnectorParam } from "./ConnectorParam";
import type { ConsentRequestMap } from "./ConsentRequestMap";
import type { Endpoint } from "./Endpoint";
import type { ExternalDatasetReference } from "./ExternalDatasetReference";
import type { RateLimitConfig } from "./RateLimitConfig";
import type { SaaSRequest } from "./SaaSRequest";

/**
 * Used to store endpoint and param configurations for a SaaS connector.
 * This is done to separate the details of how to make the API calls
 * from the data provided by a given API collection.
 *
 * The required fields for the config are converted into a Dataset which is
 * merged with the standard Fidesops Dataset to provide a complete set of dependencies
 * for the graph traversal.
 */
export type SaaSConfig = {
  fides_key: string;
  name: string;
  type: string;
  description: string;
  version: string;
  replaceable?: boolean;
  connector_params: Array<ConnectorParam>;
  external_references?: Array<ExternalDatasetReference> | null;
  client_config: ClientConfig;
  endpoints: Array<Endpoint>;
  test_request: SaaSRequest;
  data_protection_request?: SaaSRequest | null;
  rate_limit_config?: RateLimitConfig | null;
  consent_requests?: ConsentRequestMap | null;
  user_guide?: string | null;
};
