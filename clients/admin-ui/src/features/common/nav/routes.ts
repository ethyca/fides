// Home page
export const INDEX_ROUTE = "/";

// Data map group
export const ADD_SYSTEMS_ROUTE = "/add-systems";
export const ADD_SYSTEMS_MANUAL_ROUTE = "/add-systems/manual";
export const ADD_SYSTEMS_MULTIPLE_ROUTE = "/add-systems/multiple";
export const DATAMAP_ROUTE = "/datamap";
export const REPORTING_DATAMAP_ROUTE = "/reporting/datamap";
export const SYSTEM_ROUTE = "/systems";
export const EDIT_SYSTEM_ROUTE = "/systems/configure/[id]";
export const CLASSIFY_SYSTEMS_ROUTE = "/classify-systems";

// Dataset
export const DATASET_ROUTE = "/dataset";
export const DATASET_DETAIL_ROUTE = "/dataset/[datasetId]";
export const DATASET_COLLECTION_DETAIL_ROUTE =
  "/dataset/[datasetId]/[collectionName]";
export const DATASET_COLLECTION_SUBFIELD_DETAIL_ROUTE =
  "/dataset/[datasetId]/[collectionName]/[...subfieldNames]";

// Detection and discovery
export const ACTION_CENTER_ROUTE = "/data-discovery/action-center";
export const UNCATEGORIZED_SEGMENT = "[undefined]";

export const DETECTION_DISCOVERY_ACTIVITY_ROUTE = "/data-discovery/activity";
export const DATA_DETECTION_ROUTE = "/data-discovery/detection";
export const DATA_DETECTION_ROUTE_DETAIL =
  "/data-discovery/detection/[resourceUrn]";

export const DATA_DISCOVERY_ROUTE = "/data-discovery/discovery";
export const DATA_DISCOVERY_ROUTE_DETAIL =
  "/data-discovery/discovery/[resourceUrn]";

// End-to-end datasets
export const DATA_CATALOG_ROUTE = "/data-catalog";

// Privacy requests group
export const DATASTORE_CONNECTION_ROUTE = "/datastore-connection";
export const PRIVACY_REQUESTS_ROUTE = "/privacy-requests";
export const PRIVACY_REQUESTS_CONFIGURATION_ROUTE = `${PRIVACY_REQUESTS_ROUTE}/configure`;

// Consent group
export const PRIVACY_EXPERIENCE_ROUTE = "/consent/privacy-experience";
export const PRIVACY_NOTICES_ROUTE = "/consent/privacy-notices";
export const CONFIGURE_CONSENT_ROUTE = "/consent/configure";
export const ADD_MULTIPLE_VENDORS_ROUTE = "/consent/configure/add-vendors";
export const CONSENT_REPORTING_ROUTE = "/consent/reporting";

// Management group
export const PROPERTIES_ROUTE = "/properties";
export const ADD_PROPERTY_ROUTE = "/properties/add-property";
export const EDIT_PROPERTY_ROUTE = "/properties/[id]";

export const USER_MANAGEMENT_ROUTE = "/user-management";
export const INTEGRATION_MANAGEMENT_ROUTE = "/integrations";
export const ORGANIZATION_MANAGEMENT_ROUTE = "/settings/organization";
export const LOCATIONS_ROUTE = "/settings/locations";
export const REGULATIONS_ROUTE = "/settings/regulations";
export const TAXONOMY_ROUTE = "/taxonomy";
export const ABOUT_ROUTE = "/settings/about";
export const CUSTOM_FIELDS_ROUTE = "/settings/custom-fields";
export const EMAIL_TEMPLATES_ROUTE = "/settings/email-templates";
export const DOMAIN_RECORDS_ROUTE = "/settings/domain-records";
export const DOMAIN_MANAGEMENT_ROUTE = "/settings/domains";
export const GLOBAL_CONSENT_CONFIG_ROUTE = "/settings/consent";
export const MESSAGING_ROUTE = "/messaging";
export const MESSAGING_ADD_TEMPLATE_ROUTE = "/messaging/add-template";
export const MESSAGING_EDIT_ROUTE = "/messaging/[id]";

// OpenID Authentication group
export const OPENID_AUTHENTICATION_ROUTE = "/settings/openid-authentication";

export const ANT_POC_ROUTE = "/ant-poc";

export const FIDES_JS_DOCS = "/fides-js-docs";
