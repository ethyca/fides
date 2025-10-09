import { DigestConfigRequest, DigestConfigResponse } from "~/types/api";

export interface DigestConfigFormValues
  extends Omit<DigestConfigRequest, "config_metadata"> {
  id?: string; // For edit mode
}

export interface DigestConfigListItem extends DigestConfigResponse {
  // Add any computed fields if needed
}
