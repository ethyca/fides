import { ReactNode } from "react";

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
import SALESFORCE_TYPE_INFO from "~/features/integrations/integration-type-info/salesforceInfo";
import SCYLLA_TYPE_INFO from "~/features/integrations/integration-type-info/scyllaInfo";
import SNOWFLAKE_TYPE_INFO from "~/features/integrations/integration-type-info/snowflakeInfo";
import WEBSITE_INTEGRATION_TYPE_INFO from "~/features/integrations/integration-type-info/websiteInfo";
import { AccessLevel, ConnectionConfigurationResponse } from "~/types/api";
import { ConnectionCategory } from "~/types/api/models/ConnectionCategory";
import { ConnectionSystemTypeMap } from "~/types/api/models/ConnectionSystemTypeMap";
import { ConnectionType } from "~/types/api/models/ConnectionType";
import { IntegrationFeature } from "~/types/api/models/IntegrationFeature";

export type IntegrationTypeInfo = {
  placeholder: ConnectionConfigurationResponse;
  category: ConnectionCategory;
  instructions?: ReactNode;
  overview?: ReactNode;
  description?: ReactNode;
  tags: string[];
  enabledFeatures: IntegrationFeature[];
};

// Define SaaS integrations
export const SAAS_INTEGRATIONS: IntegrationTypeInfo[] = [SALESFORCE_TYPE_INFO];

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
  [ConnectionType.MANUAL_TASK]: MANUAL_TYPE_INFO,
};

export const INTEGRATION_TYPE_LIST: IntegrationTypeInfo[] = [
  ...Object.values(INTEGRATION_TYPE_MAP),
  ...SAAS_INTEGRATIONS,
];

export const SUPPORTED_INTEGRATIONS = [
  ...Object.keys(INTEGRATION_TYPE_MAP),
  ConnectionType.SAAS, // Enable SAAS integrations for Phase 1
];

/**
 * Generate IntegrationTypeInfo from ConnectionSystemTypeMap data
 * Now leverages enhanced display metadata from backend SAAS configs
 */
const generateSaasIntegrationInfo = (
  connectionType: ConnectionSystemTypeMap,
): IntegrationTypeInfo => {
  return {
    placeholder: {
      name: connectionType.human_readable,
      key: `${connectionType.identifier}_placeholder`,
      connection_type: ConnectionType.SAAS,
      saas_config: {
        fides_key: connectionType.identifier,
        name: connectionType.human_readable,
        type: connectionType.identifier,
      },
      access: AccessLevel.WRITE,
      created_at: "",
    },
    // Use backend-provided display metadata with simple fallback
    category: connectionType.category || ConnectionCategory.CUSTOM,
    tags: connectionType.tags || ["API", "Integration"], // Basic default tags if not provided
    enabledFeatures: connectionType.enabled_features || [
      IntegrationFeature.DSR_AUTOMATION,
    ], // Default to DSR automation
  };
};

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
  enabledFeatures: [] as IntegrationFeature[],
};

const getIntegrationTypeInfo = (
  type: ConnectionType | undefined,
  saasType?: string,
  connectionTypes?: ConnectionSystemTypeMap[],
): IntegrationTypeInfo => {
  if (!type) {
    return EMPTY_TYPE;
  }

  if (type === ConnectionType.SAAS && saasType) {
    // First, check if backend provides enhanced config-based data
    if (connectionTypes) {
      const connectionType = connectionTypes.find(
        (ct) => ct.identifier === saasType,
      );
      if (connectionType) {
        const configBasedInfo = generateSaasIntegrationInfo(connectionType);

        // If there's a hardcoded integration (like Salesforce), merge in the overview component
        // but prefer backend config data for category, tags, and features
        const saasIntegration = SAAS_INTEGRATIONS.find(
          (integration) =>
            integration.placeholder.saas_config?.type === saasType,
        );
        if (saasIntegration && saasIntegration.overview) {
          return {
            ...configBasedInfo,
            overview: saasIntegration.overview, // Keep rich React content for complex integrations
          };
        }

        return configBasedInfo;
      }
    }

    // Fallback to hardcoded integrations if backend data is not available
    const saasIntegration = SAAS_INTEGRATIONS.find(
      (integration) => integration.placeholder.saas_config?.type === saasType,
    );
    if (saasIntegration) {
      return saasIntegration;
    }
  }

  if (type !== ConnectionType.SAAS) {
    const integration = INTEGRATION_TYPE_MAP[type];
    if (integration) {
      return integration;
    }
  }

  return EMPTY_TYPE;
};

export default getIntegrationTypeInfo;
