/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ActionType } from "./ActionType";
import type { BigQueryDocsSchema } from "./BigQueryDocsSchema";
import type { DynamicErasureEmailDocsSchema } from "./DynamicErasureEmailDocsSchema";
import type { DynamoDBDocsSchema } from "./DynamoDBDocsSchema";
import type { EmailDocsSchema } from "./EmailDocsSchema";
import type { FidesDocsSchema } from "./FidesDocsSchema";
import type { GoogleCloudSQLMySQLDocsSchema } from "./GoogleCloudSQLMySQLDocsSchema";
import type { GoogleCloudSQLPostgresDocsSchema } from "./GoogleCloudSQLPostgresDocsSchema";
import type { ManualWebhookDocsSchema } from "./ManualWebhookDocsSchema";
import type { MariaDBDocsSchema } from "./MariaDBDocsSchema";
import type { MongoDBDocsSchema } from "./MongoDBDocsSchema";
import type { MSSQLDocsSchema } from "./MSSQLDocsSchema";
import type { MySQLDocsSchema } from "./MySQLDocsSchema";
import type { PostgreSQLDocsSchema } from "./PostgreSQLDocsSchema";
import type { RDSMySQLDocsSchema } from "./RDSMySQLDocsSchema";
import type { RDSPostgresDocsSchema } from "./RDSPostgresDocsSchema";
import type { RedshiftDocsSchema } from "./RedshiftDocsSchema";
import type { S3DocsSchema } from "./S3DocsSchema";
import type { SaaSSchema } from "./SaaSSchema";
import type { ScyllaDocsSchema } from "./ScyllaDocsSchema";
import type { SnowflakeDocsSchema } from "./SnowflakeDocsSchema";
import type { SovrnDocsSchema } from "./SovrnDocsSchema";
import type { TimescaleDocsSchema } from "./TimescaleDocsSchema";

export type SaasConnectionTemplateValuesExtended = {
  name?: string | null;
  key?: string | null;
  description?: string | null;
  secrets:
    | BigQueryDocsSchema
    | DynamicErasureEmailDocsSchema
    | DynamoDBDocsSchema
    | EmailDocsSchema
    | FidesDocsSchema
    | GoogleCloudSQLMySQLDocsSchema
    | GoogleCloudSQLPostgresDocsSchema
    | ManualWebhookDocsSchema
    | MariaDBDocsSchema
    | MongoDBDocsSchema
    | MSSQLDocsSchema
    | MySQLDocsSchema
    | RDSMySQLDocsSchema
    | RDSPostgresDocsSchema
    | PostgreSQLDocsSchema
    | RedshiftDocsSchema
    | S3DocsSchema
    | SaaSSchema
    | ScyllaDocsSchema
    | SnowflakeDocsSchema
    | SovrnDocsSchema
    | TimescaleDocsSchema;
  instance_key: string;
  enabled_actions: Array<ActionType>;
};
