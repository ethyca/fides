import { ConnectionType } from "~/types/api";

export const AWS_CONNECTION_TYPES: ReadonlySet<ConnectionType> = new Set([
  ConnectionType.AWS,
  ConnectionType.S3,
  ConnectionType.RDS_MYSQL,
  ConnectionType.RDS_POSTGRES,
  ConnectionType.DYNAMODB,
  ConnectionType.REDSHIFT,
]);

export const SERVICE_FILTER_OPTIONS: { label: string; value: string }[] = [
  { label: "All services", value: "all" },
  { label: "S3", value: "s3" },
  { label: "RDS", value: "rds" },
  { label: "Lambda", value: "lambda" },
  { label: "DynamoDB", value: "dynamodb" },
  { label: "Redshift", value: "redshift" },
  { label: "SageMaker", value: "sagemaker" },
];

export const REGION_FILTER_OPTIONS: { label: string; value: string }[] = [
  { label: "All regions", value: "all" },
  { label: "us-east-1", value: "us-east-1" },
  { label: "us-west-2", value: "us-west-2" },
  { label: "eu-west-1", value: "eu-west-1" },
];

export type ResourceServiceFilter = string;
