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
import SALESFORCE_TYPE_INFO from "~/features/integrations/integration-type-info/salesforceInfo";
import SCYLLA_TYPE_INFO from "~/features/integrations/integration-type-info/scyllaInfo";
import SNOWFLAKE_TYPE_INFO from "~/features/integrations/integration-type-info/snowflakeInfo";
import WEBSITE_INTEGRATION_TYPE_INFO from "~/features/integrations/integration-type-info/websiteInfo";
import { IntegrationFeatureEnum } from "~/features/integrations/IntegrationFeatureEnum";
import {
  AccessLevel,
  ConnectionConfigurationResponse,
  ConnectionSystemTypeMap,
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
 * Infer category from SAAS integration identifier/type
 */
const inferCategoryFromType = (identifier: string): ConnectionCategory => {
  const type = identifier.toLowerCase();

  // CRM systems
  if (
    type.includes("salesforce") ||
    type.includes("hubspot") ||
    type.includes("pipedrive") ||
    type.includes("zendesk") ||
    type.includes("intercom") ||
    type.includes("freshworks") ||
    type.includes("kustomer") ||
    type.includes("gorgias") ||
    type.includes("gladly") ||
    type.includes("outreach") ||
    type.includes("greenhouse")
  ) {
    return ConnectionCategory.CRM;
  }

  // E-commerce platforms
  if (
    type.includes("shopify") ||
    type.includes("stripe") ||
    type.includes("square") ||
    type.includes("braintree") ||
    type.includes("adyen") ||
    type.includes("recurly") ||
    type.includes("recharge") ||
    type.includes("saleor") ||
    type.includes("aftership") ||
    type.includes("shipstation") ||
    type.includes("vend") ||
    type.includes("doordash")
  ) {
    return ConnectionCategory.ECOMMERCE;
  }

  // Marketing/Email platforms
  if (
    type.includes("mailchimp") ||
    type.includes("sendgrid") ||
    type.includes("klaviyo") ||
    type.includes("braze") ||
    type.includes("iterable") ||
    type.includes("attentive") ||
    type.includes("sparkpost") ||
    type.includes("oracle_responsys") ||
    type.includes("marigold") ||
    type.includes("mailchimp_transactional") ||
    type.includes("friendbuy") ||
    type.includes("talkable") ||
    type.includes("yotpo") ||
    type.includes("powerreviews") ||
    type.includes("unbounce") ||
    type.includes("digioh") ||
    type.includes("wunderkind") ||
    type.includes("snap")
  ) {
    return ConnectionCategory.MARKETING;
  }

  // Analytics platforms
  if (
    type.includes("analytics") ||
    type.includes("amplitude") ||
    type.includes("heap") ||
    type.includes("segment") ||
    type.includes("datadog") ||
    type.includes("sentry") ||
    type.includes("fullstory") ||
    type.includes("statsig") ||
    type.includes("google_analytics") ||
    type.includes("universal_analytics") ||
    type.includes("rollbar") ||
    type.includes("domo") ||
    type.includes("appsflyer") ||
    type.includes("simon_data") ||
    type.includes("splash")
  ) {
    return ConnectionCategory.ANALYTICS;
  }

  // Communication platforms
  if (
    type.includes("slack") ||
    type.includes("twilio") ||
    type.includes("aircall") ||
    type.includes("gong") ||
    type.includes("ada_chatbot") ||
    type.includes("sprig") ||
    type.includes("typeform") ||
    type.includes("surveymonkey") ||
    type.includes("alchemer") ||
    type.includes("qualtrics") ||
    type.includes("delighted") ||
    type.includes("iterate")
  ) {
    return ConnectionCategory.COMMUNICATION;
  }

  // Payment platforms
  if (
    type.includes("stripe") ||
    type.includes("square") ||
    type.includes("braintree") ||
    type.includes("adyen") ||
    type.includes("recurly") ||
    type.includes("boostr")
  ) {
    return ConnectionCategory.PAYMENTS;
  }

  // Data warehouse/storage
  if (
    type.includes("warehouse") ||
    type.includes("domo") ||
    type.includes("bigquery")
  ) {
    return ConnectionCategory.DATA_WAREHOUSE;
  }

  // Website/tracking
  if (
    type.includes("website") ||
    type.includes("tracking") ||
    type.includes("web")
  ) {
    return ConnectionCategory.WEBSITE;
  }

  // Identity providers
  if (
    type.includes("auth0") ||
    type.includes("firebase_auth") ||
    type.includes("stytch")
  ) {
    return ConnectionCategory.IDENTITY_PROVIDER;
  }

  // Default to CRM for business applications that don't fit other categories
  return ConnectionCategory.CRM;
};

/**
 * Generate IntegrationTypeInfo from ConnectionSystemTypeMap data
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
    category: inferCategoryFromType(connectionType.identifier),
    tags: ["API", "Integration"], // Basic default tags
    enabledFeatures: [IntegrationFeatureEnum.DATA_DISCOVERY], // All SAAS get data discovery like Salesforce
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
  enabledFeatures: [] as IntegrationFeatureEnum[],
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
    // First, check if there's a hardcoded integration (like Salesforce)
    const saasIntegration = SAAS_INTEGRATIONS.find(
      (integration) => integration.placeholder.saas_config?.type === saasType,
    );
    if (saasIntegration) {
      return saasIntegration;
    }

    // If not found in hardcoded integrations, generate from connection types data
    if (connectionTypes) {
      const connectionType = connectionTypes.find(
        (ct) => ct.identifier === saasType,
      );
      if (connectionType) {
        return generateSaasIntegrationInfo(connectionType);
      }
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
