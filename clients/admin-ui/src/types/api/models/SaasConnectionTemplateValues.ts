/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { BigQueryDocsSchema } from "./BigQueryDocsSchema";
import type { DynamoDBDocsSchema } from "./DynamoDBDocsSchema";
import type { EmailDocsSchema } from "./EmailDocsSchema";
import type { FidesDocsSchema } from "./FidesDocsSchema";
import type { GoogleCloudSQLMySQLDocsSchema } from "./GoogleCloudSQLMySQLDocsSchema";
import type { GoogleCloudSQLPostgresDocsSchema } from "./GoogleCloudSQLPostgresDocsSchema";
import type { ManualWebhookSchemaforDocs } from "./ManualWebhookSchemaforDocs";
import type { MariaDBDocsSchema } from "./MariaDBDocsSchema";
import type { MongoDBDocsSchema } from "./MongoDBDocsSchema";
import type { MSSQLDocsSchema } from "./MSSQLDocsSchema";
import type { MySQLDocsSchema } from "./MySQLDocsSchema";
import type { PostgreSQLDocsSchema } from "./PostgreSQLDocsSchema";
import type { RedshiftDocsSchema } from "./RedshiftDocsSchema";
import type { S3DocsSchema } from "./S3DocsSchema";
import type { SaaSSchema } from "./SaaSSchema";
import type { ScyllaDocsSchema } from "./ScyllaDocsSchema";
import type { SnowflakeDocsSchema } from "./SnowflakeDocsSchema";
import type { SovrnDocsSchema } from "./SovrnDocsSchema";
import type { TimescaleDocsSchema } from "./TimescaleDocsSchema";

/**
 * Schema with values to create both a Saas ConnectionConfig and DatasetConfig from a template
 */
export type SaasConnectionTemplateValues = {
  name?: string | null;
  key?: string | null;
  description?: string | null;
  secrets:
    | MongoDBDocsSchema
    | PostgreSQLDocsSchema
    | MySQLDocsSchema
    | GoogleCloudSQLMySQLDocsSchema
    | GoogleCloudSQLPostgresDocsSchema
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
    | DynamoDBDocsSchema
    | S3DocsSchema
    | ScyllaDocsSchema;
  instance_key: string;
};
