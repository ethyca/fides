import { Field, StagedResourceAPIResponse } from "~/types/api";

/**
 * Utility class for a staged resource of unknown type
 */
export type DiscoveryMonitorItem = StagedResourceAPIResponse &
  Omit<Partial<Field>, "schema_name" | "parent_table_urn" | "table_name"> & {
    schema_name?: string | null;
    parent_table_urn?: string | null;
    table_name?: string | null;
  };
