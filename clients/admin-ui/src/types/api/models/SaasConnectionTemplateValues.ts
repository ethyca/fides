/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { BigQueryDocsSchema } from "./BigQueryDocsSchema";
import type { ConsentEmailDocsSchema } from "./ConsentEmailDocsSchema";
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
import type { TimescaleDocsSchema } from "./TimescaleDocsSchema";

/**
 * Schema with values to create both a Saas ConnectionConfig and DatasetConfig from a template
 */
export type SaasConnectionTemplateValues = {
  name: string;
  key?: string;
  description?: string;
  secrets:
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
    | ConsentEmailDocsSchema;
  instance_key: string;
};
