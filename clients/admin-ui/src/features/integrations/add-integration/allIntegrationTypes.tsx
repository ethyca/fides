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

const integrationTypeLookup: { [K in ConnectionType]?: IntegrationTypeInfo } = {
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
    tags: ["Database", "DynamoDB", "Tag 3", "Tag 4"],
  },
};

export const integrationTypeList: IntegrationTypeInfo[] = [
  {
    placeholder: DYNAMO_PLACEHOLDER,
    category: ConnectionCategory.DATABASE,
    copy: <DynamoOverview />,
    tags: ["Database", "DynamoDB", "Tag 3", "Tag 4"],
  },
  {
    placeholder: BQ_PLACEHOLDER,
    category: ConnectionCategory.DATA_WAREHOUSE,
    copy: <BigQueryOverview />,
    tags: BIGQUERY_TAGS,
  },
];

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
  return integrationTypeLookup[type] ?? NO_TYPE;
};

export default getIntegrationTypeInfo;
