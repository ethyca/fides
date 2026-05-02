import { CONNECTOR_LOGOS_PATH } from "~/features/datastore-connections/constants";

// Known AWS service types. Unknown services fall back to the raw string label
// and the Cloud icon. Add new entries here as new AWS integrations are added.
const SERVICE_INFO: Record<string, { icon: string; label: string }> = {
  s3: { icon: "S3-resource.svg", label: "S3" },
  rds: { icon: "RDS-resource.svg", label: "RDS" },
  dynamodb: { icon: "DynamoDB-resource.svg", label: "DynamoDB" },
};

export const getServiceIconUrl = (service?: string): string | undefined => {
  if (!service) {
    return undefined;
  }
  const info = SERVICE_INFO[service.toLowerCase()];
  return info ? `${CONNECTOR_LOGOS_PATH}${info.icon}` : undefined;
};

export const getServiceLabel = (service: string): string => {
  return SERVICE_INFO[service.toLowerCase()]?.label ?? service;
};
