import { ReactNode } from "react";

import { ConnectionCategory } from "~/features/integrations/ConnectionCategory";
import BIGQUERY_TYPE_INFO from "~/features/integrations/integration-copy/bigqueryOverviewCopy";
import DYNAMO_TYPE_INFO from "~/features/integrations/integration-copy/dynamoOverviewCopy";
import S3_TYPE_INFO from "~/features/integrations/integration-copy/s3OverviewCopy";
import SCYLLA_TYPE_INFO from "~/features/integrations/integration-copy/scyllaOverviewCopy";
import {
  AccessLevel,
  ConnectionConfigurationResponse,
  ConnectionType,
} from "~/types/api";

export type IntegrationTypeInfo = {
  placeholder: ConnectionConfigurationResponse;
  category: ConnectionCategory;
  overview?: ReactNode;
  instructions?: ReactNode;
  tags: string[];
};

const INTEGRATION_TYPE_MAP: { [K in ConnectionType]?: IntegrationTypeInfo } = {
  [ConnectionType.BIGQUERY]: BIGQUERY_TYPE_INFO,
  [ConnectionType.DYNAMODB]: DYNAMO_TYPE_INFO,
  [ConnectionType.SCYLLA]: SCYLLA_TYPE_INFO,
  [ConnectionType.S3]: S3_TYPE_INFO,
};

export const integrationTypeList: IntegrationTypeInfo[] =
  Object.values(INTEGRATION_TYPE_MAP);

export const supportedIntegrations = Object.keys(INTEGRATION_TYPE_MAP);

const EMPTY_TYPE = {
  placeholder: {
    name: "",
    key: "placeholder",
    connection_type: ConnectionType.MANUAL,
    access: AccessLevel.READ,
    created_at: "",
  },
  category: ConnectionCategory.DATA_WAREHOUSE,
  tags: [],
};

const getIntegrationTypeInfo = (
  type: ConnectionType | undefined
): IntegrationTypeInfo => {
  if (!type) {
    return EMPTY_TYPE;
  }
  return INTEGRATION_TYPE_MAP[type] ?? EMPTY_TYPE;
};

export default getIntegrationTypeInfo;
