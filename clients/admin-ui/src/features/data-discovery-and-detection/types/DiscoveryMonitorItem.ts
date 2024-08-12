import { Database, Field, Schema, StagedResource, Table } from "~/types/api";

export type DiscoveryMonitorItem = StagedResource & {
  system?: string;
} & Partial<Database & Schema & Table & Field>;
