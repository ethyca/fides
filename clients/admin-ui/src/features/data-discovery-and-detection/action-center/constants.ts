export enum DiscoveryStatusDisplayNames {
  WITH_CONSENT = "With consent",
  WITHOUT_CONSENT = "Without consent",
  EXEMPT = "Exempt",
  UNKNOWN = "Unknown",
  PRE_CONSENT = "Pre-consent",
  CMP_ERROR = "CMP error",
  NOT_APPLICABLE = "Not applicable",
}

export enum DiscoveredAssetsColumnKeys {
  NAME = "name",
  RESOURCE_TYPE = "resource_type",
  SYSTEM = "system",
  DATA_USES = "data_uses",
  LOCATIONS = "locations",
  DOMAIN = "domain",
  PAGE = "page",
  CONSENT_AGGREGATED = "consent_aggregated",
  ACTIONS = "actions",
}

export enum DiscoveredSystemAggregateColumnKeys {
  SYSTEM_NAME = "system_name",
  TOTAL_UPDATES = "total_updates",
  DATA_USE = "data_use",
  LOCATIONS = "locations",
  DOMAINS = "domains",
  ACTIONS = "actions",
}

export enum ConsentBreakdownColumnKeys {
  LOCATION = "location",
  PAGE = "page",
}
