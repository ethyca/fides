import { CONNECTOR_LOGOS_PATH } from "~/features/datastore-connections/constants";

// Known AWS service types. Unknown services fall back to the raw string label
// and the Cloud icon. Add new entries here as new AWS integrations are added.
// `typeLabel` is the human-readable resource type shown in the details tray.
const SERVICE_INFO: Record<
  string,
  { icon: string; label: string; typeLabel: string }
> = {
  s3: { icon: "s3.svg", label: "S3", typeLabel: "Amazon S3 Bucket" },
  rds: { icon: "rds.svg", label: "RDS", typeLabel: "Amazon RDS Instance" },
  dynamodb: {
    icon: "dynamodb.svg",
    label: "DynamoDB",
    typeLabel: "Amazon DynamoDB Table",
  },
  redshift: {
    icon: "redshift.svg",
    label: "Redshift",
    typeLabel: "Amazon Redshift Cluster",
  },
  lambda: { icon: "", label: "Lambda", typeLabel: "AWS Lambda Function" },
};

export const getServiceIconUrl = (service?: string): string | undefined => {
  if (!service) {
    return undefined;
  }
  const info = SERVICE_INFO[service.toLowerCase()];
  return info?.icon ? `${CONNECTOR_LOGOS_PATH}${info.icon}` : undefined;
};

export const getServiceLabel = (service: string): string => {
  return SERVICE_INFO[service.toLowerCase()]?.label ?? service;
};

/** Human-readable resource type, e.g. "Amazon S3 Bucket". */
export const getServiceTypeLabel = (service?: string): string => {
  if (!service) {
    return "—";
  }
  return SERVICE_INFO[service.toLowerCase()]?.typeLabel ?? service;
};
