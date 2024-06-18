import { ReactNode } from "react";

import BigQueryOverview from "~/features/integrations/integration-copy/bigqueryOverviewCopy";
import DynamoOverview from "~/features/integrations/integration-copy/dynamoOverviewCopy";
import {
  AccessLevel,
  ConnectionConfigurationResponse,
  ConnectionType,
} from "~/types/api";

export enum ConnectionCategory {
  DATA_WAREHOUSE = "Data Warehouse",
  DATABASE = "Database",
}

export type IntegrationTypeInfo = {
  placeholder: ConnectionConfigurationResponse;
  category: ConnectionCategory;
  copy?: ReactNode;
  tags: string[];
};

const BQ_PLACEHOLDER = {
  name: "Google BigQuery",
  key: "bq_placeholder",
  connection_type: ConnectionType.BIGQUERY,
  access: AccessLevel.READ,
  created_at: "",
};

const BIGQUERY_TAGS = ["Data Warehouse", "BigQuery", "Discovery", "Inventory"];

const DYNAMO_PLACEHOLDER = {
  name: "DynamoDB",
  key: "dynamo_placeholder",
  connection_type: ConnectionType.DYNAMODB,
  access: AccessLevel.READ,
  created_at: "",
};

const DYNAMO_TAGS = ["Database", "DynamoDB", "Tag 3", "Tag 4"];

const SCYLLA_PLACEHOLDER = {
  name: "Scylla",
  key: "scylla_placeholder",
  connection_type: ConnectionType.SCYLLA,
  access: AccessLevel.READ,
  created_at: "",
};

const SCYLLA_TAGS = ["Database", "DynamoDB", "Tag 3", "Tag 4"];

const S3_PLACEHOLDER = {
  name: "Amazon S3",
  key: "s3_placeholder",
  connection_type: ConnectionType.S3,
  access: AccessLevel.READ,
  created_at: "",
};

const S3_TAGS = ["Data Warehouse", "S3", "Tag 3", "Tag 4"];

const INTEGRATION_TYPE_MAP: { [K in ConnectionType]?: IntegrationTypeInfo } = {
  [ConnectionType.BIGQUERY]: {
    placeholder: BQ_PLACEHOLDER,
    category: ConnectionCategory.DATA_WAREHOUSE,
    copy: <BigQueryOverview />,
    tags: BIGQUERY_TAGS,
  },
  [ConnectionType.DYNAMODB]: {
    placeholder: DYNAMO_PLACEHOLDER,
    category: ConnectionCategory.DATABASE,
    copy: <DynamoOverview />,
    tags: DYNAMO_TAGS,
  },
  [ConnectionType.SCYLLA]: {
    placeholder: SCYLLA_PLACEHOLDER,
    category: ConnectionCategory.DATABASE,
    copy: <DynamoOverview />,
    tags: SCYLLA_TAGS,
  },
  [ConnectionType.S3]: {
    placeholder: S3_PLACEHOLDER,
    category: ConnectionCategory.DATA_WAREHOUSE,
    copy: <DynamoOverview />,
    tags: S3_TAGS,
  },
};

export const integrationTypeList: IntegrationTypeInfo[] =
  Object.values(INTEGRATION_TYPE_MAP);

const NO_TYPE = {
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
    return NO_TYPE;
  }
  return INTEGRATION_TYPE_MAP[type] ?? NO_TYPE;
};

export default getIntegrationTypeInfo;
