import { Database, Field, Schema, StagedResource, Table } from "~/types/api";

export type DiscoveryMonitorItem = StagedResource &
  Partial<Database & Schema & Table & Field>;
