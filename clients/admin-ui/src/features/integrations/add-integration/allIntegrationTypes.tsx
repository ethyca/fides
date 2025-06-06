import { ReactNode } from "react";

import { ConnectionCategory } from "~/features/integrations/ConnectionCategory";
import BIGQUERY_TYPE_INFO from "~/features/integrations/integration-type-info/bigqueryInfo";
import DATAHUB_TYPE_INFO from "~/features/integrations/integration-type-info/datahubInfo";
import DYNAMO_TYPE_INFO from "~/features/integrations/integration-type-info/dynamoInfo";
import GOOGLE_CLOUD_SQL_MYSQL_TYPE_INFO from "~/features/integrations/integration-type-info/googleCloudSQLMySQLInfo";
import GOOGLE_CLOUD_SQL_POSTGRES_TYPE_INFO from "~/features/integrations/integration-type-info/googleCloudSQLPostgresInfo";
import MANUAL_TYPE_INFO from "~/features/integrations/integration-type-info/manualInfo";
import MICROSOFT_SQL_SERVER_TYPE_INFO from "~/features/integrations/integration-type-info/microsoftSQLServerInfo";
import MYSQL_TYPE_INFO from "~/features/integrations/integration-type-info/mySQLInfo";
import OKTA_TYPE_INFO from "~/features/integrations/integration-type-info/oktaInfo";
import POSTGRES_TYPE_INFO from "~/features/integrations/integration-type-info/postgreSQLInfo";
import RDS_MYSQL_TYPE_INFO from "~/features/integrations/integration-type-info/rdsMySQLInfo";
import RDS_POSTGRES_TYPE_INFO from "~/features/integrations/integration-type-info/rdsPostgresInfo";
import S3_TYPE_INFO from "~/features/integrations/integration-type-info/s3Info";
import SCYLLA_TYPE_INFO from "~/features/integrations/integration-type-info/scyllaInfo";
import SNOWFLAKE_TYPE_INFO from "~/features/integrations/integration-type-info/snowflakeInfo";
import WEBSITE_INTEGRATION_TYPE_INFO from "~/features/integrations/integration-type-info/websiteInfo";
import { IntegrationFeatureEnum } from "~/features/integrations/IntegrationFeatureEnum";
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
  enabledFeatures: IntegrationFeatureEnum[];
};

const INTEGRATION_TYPE_MAP: { [K in ConnectionType]?: IntegrationTypeInfo } = {
  [ConnectionType.BIGQUERY]: BIGQUERY_TYPE_INFO,
  [ConnectionType.DATAHUB]: DATAHUB_TYPE_INFO,
  [ConnectionType.DYNAMODB]: DYNAMO_TYPE_INFO,
  [ConnectionType.GOOGLE_CLOUD_SQL_MYSQL]: GOOGLE_CLOUD_SQL_MYSQL_TYPE_INFO,
  [ConnectionType.GOOGLE_CLOUD_SQL_POSTGRES]:
    GOOGLE_CLOUD_SQL_POSTGRES_TYPE_INFO,
  [ConnectionType.MSSQL]: MICROSOFT_SQL_SERVER_TYPE_INFO,
  [ConnectionType.OKTA]: OKTA_TYPE_INFO,
  [ConnectionType.RDS_MYSQL]: RDS_MYSQL_TYPE_INFO,
  [ConnectionType.RDS_POSTGRES]: RDS_POSTGRES_TYPE_INFO,
  [ConnectionType.S3]: S3_TYPE_INFO,
  [ConnectionType.SCYLLA]: SCYLLA_TYPE_INFO,
  [ConnectionType.SNOWFLAKE]: SNOWFLAKE_TYPE_INFO,
  [ConnectionType.MYSQL]: MYSQL_TYPE_INFO,
  [ConnectionType.WEBSITE]: WEBSITE_INTEGRATION_TYPE_INFO,
  [ConnectionType.POSTGRES]: POSTGRES_TYPE_INFO,
  [ConnectionType.MANUAL_WEBHOOK]: MANUAL_TYPE_INFO,
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
  enabledFeatures: [] as IntegrationFeatureEnum[],
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
