import { ReactNode } from "react";

import { ConnectionCategory } from "~/features/integrations/ConnectionCategory";
import BIGQUERY_TYPE_INFO from "~/features/integrations/integration-type-info/bigqueryInfo";
import DATAHUB_TYPE_INFO from "~/features/integrations/integration-type-info/datahubInfo";
import DYNAMO_TYPE_INFO from "~/features/integrations/integration-type-info/dynamoInfo";
import GOOGLE_CLOUD_SQL_MYSQL_TYPE_INFO from "~/features/integrations/integration-type-info/googleCloudSQLMySQLInfo";
import GOOGLE_CLOUD_SQL_POSTGRES_TYPE_INFO from "~/features/integrations/integration-type-info/googleCloudSQLPostgresInfo";
import MICROSOFT_SQL_SERVER_TYPE_INFO from "~/features/integrations/integration-type-info/microsoftSQLServerInfo";
import MYSQL_TYPE_INFO from "~/features/integrations/integration-type-info/mySQLInfo";
import POSTGRES_TYPE_INFO from "~/features/integrations/integration-type-info/postgreSQLInfo";
import RDS_MYSQL_TYPE_INFO from "~/features/integrations/integration-type-info/rdsMySQLInfo";
import RDS_POSTGRES_TYPE_INFO from "~/features/integrations/integration-type-info/rdsPostgresInfo";
import S3_TYPE_INFO from "~/features/integrations/integration-type-info/s3Info";
import SALESFORCE_TYPE_INFO from "~/features/integrations/integration-type-info/salesforceInfo";
import SCYLLA_TYPE_INFO from "~/features/integrations/integration-type-info/scyllaInfo";
import SNOWFLAKE_TYPE_INFO from "~/features/integrations/integration-type-info/snowflakeInfo";
import WEBSITE_INTEGRATION_TYPE_INFO from "~/features/integrations/integration-type-info/websiteInfo";
import {
  AccessLevel,
  ConnectionConfigurationResponse,
  ConnectionType,
} from "~/types/api";

export type IntegrationTypeInfo = {
  placeholder: ConnectionConfigurationResponse;
  category: ConnectionCategory;
  overview?: ReactNode;
  description?: ReactNode;
  instructions?: ReactNode;
  tags: string[];
};

// Define SaaS-specific integrations separately
export const SAAS_INTEGRATIONS: IntegrationTypeInfo[] = [SALESFORCE_TYPE_INFO];

const INTEGRATION_TYPE_MAP: { [K in ConnectionType]?: IntegrationTypeInfo } = {
  [ConnectionType.BIGQUERY]: BIGQUERY_TYPE_INFO,
  [ConnectionType.DATAHUB]: DATAHUB_TYPE_INFO,
  [ConnectionType.DYNAMODB]: DYNAMO_TYPE_INFO,
  [ConnectionType.GOOGLE_CLOUD_SQL_MYSQL]: GOOGLE_CLOUD_SQL_MYSQL_TYPE_INFO,
  [ConnectionType.GOOGLE_CLOUD_SQL_POSTGRES]:
    GOOGLE_CLOUD_SQL_POSTGRES_TYPE_INFO,
  [ConnectionType.MSSQL]: MICROSOFT_SQL_SERVER_TYPE_INFO,
  [ConnectionType.RDS_MYSQL]: RDS_MYSQL_TYPE_INFO,
  [ConnectionType.RDS_POSTGRES]: RDS_POSTGRES_TYPE_INFO,
  [ConnectionType.S3]: S3_TYPE_INFO,
  [ConnectionType.SCYLLA]: SCYLLA_TYPE_INFO,
  [ConnectionType.SNOWFLAKE]: SNOWFLAKE_TYPE_INFO,
  [ConnectionType.MYSQL]: MYSQL_TYPE_INFO,
  [ConnectionType.WEBSITE]: WEBSITE_INTEGRATION_TYPE_INFO,
  [ConnectionType.POSTGRES]: POSTGRES_TYPE_INFO,
};

// Include both regular integrations and SaaS integrations in the list
export const INTEGRATION_TYPE_LIST: IntegrationTypeInfo[] = [
  ...Object.values(INTEGRATION_TYPE_MAP),
  ...SAAS_INTEGRATIONS,
];

export const SUPPORTED_INTEGRATIONS = [
  ...Object.keys(INTEGRATION_TYPE_MAP),
  ConnectionType.SAAS,
];

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

  // For SAAS type, return the first SaaS integration (temporary until we have a better way to handle this)
  if (type === ConnectionType.SAAS) {
    return SAAS_INTEGRATIONS[0] ?? EMPTY_TYPE;
  }

  return INTEGRATION_TYPE_MAP[type] ?? EMPTY_TYPE;
};

export default getIntegrationTypeInfo;
