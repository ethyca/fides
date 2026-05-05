import { DiffStatus } from "./DiffStatus";
import { StagedResourceTypeValue } from "./StagedResourceTypeValue";

export type CloudInfraResourceMetadata = {
  provider: string;
  source_type: string;
  category?: string | null;
  raw_response: Record<string, unknown>;
};

export type CloudInfraStagedResource = {
  urn: string;
  name?: string | null;
  description?: string | null;
  monitor_config_id?: string | null;
  updated_at?: string | null;
  diff_status?: DiffStatus | null;
  resource_type?: StagedResourceTypeValue;
  meta?: CloudInfraResourceMetadata | null;
  service: string;
  location: string;
  cloud_account_id: string;
  source_id: string;
  tags?: Record<string, string> | null;
};
