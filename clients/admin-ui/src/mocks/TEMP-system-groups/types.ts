import { BasicSystemResponse, System } from "~/types/api";
import { PaginatedResponse } from "~/types/query-params";

export interface SystemResponseWithGroups extends BasicSystemResponse {
  groups: string[];
}

export interface PaginatedSystemsWithGroups
  extends PaginatedResponse<SystemResponseWithGroups> {}

export interface SystemUpsertWithGroups extends System {
  groups: string[];
}

export interface SystemBulkAddToGroupPayload {
  system_keys: string[];
  group_key: string;
}

export interface SystemGroupListResponse {
  items: SystemGroup[];
}

export interface SystemGroup {
  fides_key: string;
  name: string;
  color: CustomTaxonomyColor;
}

export interface SystemGroupCreate {
  name: string;
  description: string;
  color: CustomTaxonomyColor;
  systems: string[];
  data_uses: string[];
  data_steward: string;
}

export enum CustomTaxonomyColor {
  WHITE = "default",
  RED = "taxonomy_red",
  ORANGE = "taxonomy_orange",
  YELLOW = "taxonomy_yellow",
  GREEN = "taxonomy_green",
  BLUE = "taxonomy_blue",
  PURPLE = "taxonomy_purple",
  SANDSTONE = "sandstone",
  MINOS = "minos",
}
