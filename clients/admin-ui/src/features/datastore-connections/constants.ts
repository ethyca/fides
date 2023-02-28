import { ConnectionType } from "~/types/api";

/**
 * Enums
 */
export enum AccessLevel {
  READ = "read",
  WRITE = "write",
}

export enum ConnectionTestStatus {
  SUCCEEDED = "succeeded",
  FAILED = "failed",
  SKIPPED = "skipped",
}

export enum DisabledStatus {
  ACTIVE = "active",
  DISABLED = "disabled",
}

export enum SaasType {
  ADOBE_CAMPAIGN = "adobe_campaign",
  AUTH0 = "auth0",
  BRAZE = "braze",
  DATADOG = "datadog",
  DOMO = "domo",
  DOORDASH = "doordash",
  FIREBASE_AUTH = "firebase_auth",
  FRIENDBUY = "friendbuy",
  FRIENDBUY_NEXTGEN = "friendbuy_nextgen",
  FULLSTORY = "fullstory",
  GOOGLE_ANALYTICS = "google_analytics",
  HUBSPOT = "hubspot",
  JIRA = "jira",
  MAILCHIMP = "mailchimp",
  MAILCHIMP_TRANSACTIONAL = "mailchimp_transactional",
  OUTREACH = "outreach",
  RECHARGE = "recharge",
  ROLLBAR = "rollbar",
  SALESFORCE = "salesforce",
  SEGMENT = "segment",
  SENDGRID = "sendgrid",
  SENTRY = "sentry",
  SHOPIFY = "shopify",
  SLACK_ENTERPRISE = "slack_enterprise",
  SQUARE = "square",
  STRIPE = "stripe",
  TWILIO_CONVERSATIONS = "twilio_conversations",
  UNIVERSAL_ANALYTICS = "universal_analytics",
  VEND = "vend",
  WUNDERKIND = "wunderkind",
  ZENDESK = "zendesk",
}

export enum TestingStatus {
  PASSED = "passed",
  FAILED = "failed",
  UNTESTED = "untested",
}

/**
 * Relative folder path for connector logo images
 */
export const CONNECTOR_LOGOS_PATH = "/images/connector-logos/";

/**
 * List of connection type image key/value pairs
 */
export const CONNECTION_TYPE_LOGO_MAP = new Map<
  ConnectionType | SaasType,
  string
>([
  [ConnectionType.BIGQUERY, "bigquery.svg"],
  [ConnectionType.MANUAL_WEBHOOK, "manual_webhook.svg"],
  [ConnectionType.MARIADB, "mariadb.svg"],
  [ConnectionType.MONGODB, "mongodb.svg"],
  [ConnectionType.MSSQL, "sqlserver.svg"],
  [ConnectionType.MYSQL, "mysql.svg"],
  [ConnectionType.POSTGRES, "postgres.svg"],
  [ConnectionType.REDSHIFT, "redshift.svg"],
  [ConnectionType.SNOWFLAKE, "snowflake.svg"],
  [ConnectionType.TIMESCALE, "timescaledb.svg"],
  [SaasType.ADOBE_CAMPAIGN, "adobe.svg"],
  [SaasType.AUTH0, "auth0.svg"],
  [SaasType.BRAZE, "braze.svg"],
  [SaasType.DATADOG, "datadog.svg"],
  [SaasType.DOMO, "domo.svg"],
  [SaasType.DOORDASH, "doordash.svg"],
  [SaasType.FIREBASE_AUTH, "firebase.svg"],
  [SaasType.FRIENDBUY, "friendbuy.svg"],
  [SaasType.FRIENDBUY_NEXTGEN, "friendbuy.svg"],
  [SaasType.FULLSTORY, "fullstory.svg"],
  [SaasType.GOOGLE_ANALYTICS, "google_analytics.svg"],
  [SaasType.HUBSPOT, "hubspot.svg"],
  [SaasType.JIRA, "jira.svg"],
  [SaasType.MAILCHIMP, "mailchimp.svg"],
  [SaasType.MAILCHIMP_TRANSACTIONAL, "mandrill.svg"],
  [SaasType.OUTREACH, "outreach.svg"],
  [SaasType.RECHARGE, "recharge.svg"],
  [SaasType.ROLLBAR, "rollbar.svg"],
  [SaasType.SALESFORCE, "salesforce.svg"],
  [SaasType.SEGMENT, "segment.svg"],
  [SaasType.SENDGRID, "sendgrid.svg"],
  [SaasType.SENTRY, "sentry.svg"],
  [SaasType.SHOPIFY, "shopify.svg"],
  [SaasType.SLACK_ENTERPRISE, "slack.svg"],
  [ConnectionType.SOVRN, "sovrn.svg"],
  [SaasType.SQUARE, "square.svg"],
  [SaasType.STRIPE, "stripe.svg"],
  [SaasType.TWILIO_CONVERSATIONS, "twilio.svg"],
  [SaasType.UNIVERSAL_ANALYTICS, "google_analytics.svg"],
  [SaasType.VEND, "vend.svg"],
  [SaasType.WUNDERKIND, "wunderkind.svg"],
  [SaasType.ZENDESK, "zendesk.svg"],
]);

/**
 * Fallback connector image path if original src path doesn't exist
 */
export const FALLBACK_CONNECTOR_LOGOS_PATH = `${CONNECTOR_LOGOS_PATH}ethyca.svg`;
