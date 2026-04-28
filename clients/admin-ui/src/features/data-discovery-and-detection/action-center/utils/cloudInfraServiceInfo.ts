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
  return info ? `/images/connector-logos/${info.icon}` : undefined;
};

export const getServiceLabel = (service: string): string => {
  return SERVICE_INFO[service.toLowerCase()]?.label ?? service;
};
