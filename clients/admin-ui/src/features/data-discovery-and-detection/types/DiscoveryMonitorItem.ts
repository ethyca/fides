import { Field, StagedResourceAPIResponse } from "~/types/api";

/**
 * Utility class for a staged resource of unknown type
 */
export type DiscoveryMonitorItem = StagedResourceAPIResponse & Partial<Field>;
