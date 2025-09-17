import { ConsentStatus } from "~/types/api";

export const DiscoveryStatusDisplayNames: Record<ConsentStatus, string> = {
  [ConsentStatus.WITH_CONSENT]: "With consent",
  [ConsentStatus.WITHOUT_CONSENT]: "Without consent",
  [ConsentStatus.EXEMPT]: "Exempt",
  [ConsentStatus.UNKNOWN]: "Unknown",
  [ConsentStatus.PRE_CONSENT]: "Pre-Consent",
  [ConsentStatus.CMP_ERROR]: "CMP failure",
  [ConsentStatus.NOT_APPLICABLE]: "Not applicable",
};

export const DiscoveryStatusDescriptions: Record<ConsentStatus, string> = {
  [ConsentStatus.WITH_CONSENT]:
    "Asset was detected after the user gave consent",
  [ConsentStatus.WITHOUT_CONSENT]:
    "Asset was detected without any consent. Click the info icon for more details.",
  [ConsentStatus.EXEMPT]: "Asset is valid regardless of consent",
  [ConsentStatus.UNKNOWN]:
    "Did not find consent information for this asset. You may need to re-run the monitor.",
  [ConsentStatus.PRE_CONSENT]:
    "Assets loaded before the user had a chance to give consent. This violates opt-in compliance requirements if your CMP is configured for explicit consent.",
  [ConsentStatus.CMP_ERROR]:
    "The Consent Management Platform (CMP) was not detected when the service ran. It likely failed to load or wasn't available.",
  [ConsentStatus.NOT_APPLICABLE]: "No privacy notices apply to this asset",
};

export enum ConsentStatusType {
  SUCCESS = "success",
  ERROR = "error",
  IGNORE = "ignore",
}

export const DiscoveryStatusTypeMapping: Record<
  ConsentStatus,
  ConsentStatusType
> = {
  [ConsentStatus.WITH_CONSENT]: ConsentStatusType.SUCCESS,
  [ConsentStatus.WITHOUT_CONSENT]: ConsentStatusType.ERROR,
  [ConsentStatus.PRE_CONSENT]: ConsentStatusType.ERROR,
  [ConsentStatus.CMP_ERROR]: ConsentStatusType.ERROR,
  [ConsentStatus.EXEMPT]: ConsentStatusType.IGNORE,
  [ConsentStatus.UNKNOWN]: ConsentStatusType.IGNORE,
  [ConsentStatus.NOT_APPLICABLE]: ConsentStatusType.IGNORE,
};

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
