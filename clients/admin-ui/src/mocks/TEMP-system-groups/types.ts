import { System } from "~/types/api";

export interface SystemUpsertWithGroups extends System {
  groups: string[];
}

export interface SystemBulkAddToGroupPayload {
  system_keys: string[];
  group_key: string;
}
