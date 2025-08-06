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

export interface SystemGroupListResponse {
  items: SystemGroup[];
}

export interface SystemGroup {
  fides_key: string;
  name: string;
  color: CustomTaxonomyColor;
}

export enum CustomTaxonomyColor {
  WHITE = "bg-taxonomy-white",
  RED = "bg-taxonomy-red",
  ORANGE = "bg-taxonomy-orange",
  YELLOW = "bg-taxonomy-yellow",
  GREEN = "bg-taxonomy-green",
  BLUE = "bg-taxonomy-blue",
  PURPLE = "bg-taxonomy-purple",
  SANDSTONE = "sandstone",
  MINOS = "minos",
}
