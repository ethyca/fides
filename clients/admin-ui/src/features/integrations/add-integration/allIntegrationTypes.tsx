import { ReactNode } from "react";

import { ConnectionCategory } from "~/features/integrations/ConnectionCategory";
import BIGQUERY_TYPE_INFO from "~/features/integrations/integration-type-info/bigqueryInfo";
import DYNAMO_TYPE_INFO from "~/features/integrations/integration-type-info/dynamoInfo";
import GOOGLE_CLOUD_SQL_MYSQL_TYPE_INFO from "~/features/integrations/integration-type-info/googleCloudSQLMySQLInfo";
import GOOGLE_CLOUD_SQL_POSTGRES_TYPE_INFO from "~/features/integrations/integration-type-info/googleCloudSQLPostgresInfo";
import S3_TYPE_INFO from "~/features/integrations/integration-type-info/s3Info";
import SCYLLA_TYPE_INFO from "~/features/integrations/integration-type-info/scyllaInfo";
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
  [ConnectionType.GOOGLE_CLOUD_SQL_MYSQL]: GOOGLE_CLOUD_SQL_MYSQL_TYPE_INFO,
  [ConnectionType.GOOGLE_CLOUD_SQL_POSTGRES]:
    GOOGLE_CLOUD_SQL_POSTGRES_TYPE_INFO,
  [ConnectionType.S3]: S3_TYPE_INFO,
  [ConnectionType.SCYLLA]: SCYLLA_TYPE_INFO,
};

export const INTEGRATION_TYPE_LIST: IntegrationTypeInfo[] =
  Object.values(INTEGRATION_TYPE_MAP);

export const SUPPORTED_INTEGRATIONS = Object.keys(INTEGRATION_TYPE_MAP);

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
  type: ConnectionType | undefined,
): IntegrationTypeInfo => {
  if (!type) {
    return EMPTY_TYPE;
  }
  return INTEGRATION_TYPE_MAP[type] ?? EMPTY_TYPE;
};

export default getIntegrationTypeInfo;
