/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { AccessLevel } from "./AccessLevel";
import type { BigQueryDocsSchema } from "./BigQueryDocsSchema";
import type { ConnectionType } from "./ConnectionType";
import type { DynamoDBDocsSchema } from "./DynamoDBDocsSchema";
import type { EmailDocsSchema } from "./EmailDocsSchema";
import type { FidesDocsSchema } from "./FidesDocsSchema";
import type { ManualWebhookSchemaforDocs } from "./ManualWebhookSchemaforDocs";
import type { MariaDBDocsSchema } from "./MariaDBDocsSchema";
import type { MongoDBDocsSchema } from "./MongoDBDocsSchema";
import type { MSSQLDocsSchema } from "./MSSQLDocsSchema";
import type { MySQLDocsSchema } from "./MySQLDocsSchema";
import type { PostgreSQLDocsSchema } from "./PostgreSQLDocsSchema";
import type { RedshiftDocsSchema } from "./RedshiftDocsSchema";
import type { SaaSSchema } from "./SaaSSchema";
import type { SnowflakeDocsSchema } from "./SnowflakeDocsSchema";
import type { SovrnDocsSchema } from "./SovrnDocsSchema";
import type { TimescaleDocsSchema } from "./TimescaleDocsSchema";

/**
 * Schema for creating a connection configuration including secrets.
 */
export type CreateConnectionConfigurationWithSecrets = {
  name: string;
  key?: string;
  connection_type: ConnectionType;
  access: AccessLevel;
  disabled?: boolean;
  description?: string;
  secrets?:
    | MongoDBDocsSchema
    | PostgreSQLDocsSchema
    | MySQLDocsSchema
    | RedshiftDocsSchema
    | SnowflakeDocsSchema
    | MSSQLDocsSchema
    | MariaDBDocsSchema
    | BigQueryDocsSchema
    | SaaSSchema
    | EmailDocsSchema
    | ManualWebhookSchemaforDocs
    | TimescaleDocsSchema
    | FidesDocsSchema
    | SovrnDocsSchema
    | DynamoDBDocsSchema;
  saas_connector_type?: string;
};
