import { Database, Field, Schema, StagedResource, Table } from "~/types/api";
/**
 * Utility class for a StagedResource of unknown type (field, database, etc.).
 */
export type DiscoveryMonitorItem = StagedResource &
  Partial<Database & Schema & Table & Field>;
