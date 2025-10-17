import { AntTreeDataNode as TreeDataNode } from "fidesui";

import { TreeResourceChangeIndicator } from "~/types/api";
import { FieldActionType } from "~/types/api/models/FieldActionType";

/**
 * Extend TreeDataNode to include the update status from the API response
 * and force the title to be a string since we use a custom title renderer
 */
export interface CustomTreeDataNode extends TreeDataNode {
  title?: string | null;
  status?: TreeResourceChangeIndicator | null;
  children?: CustomTreeDataNode[];
}

export type FieldActionTypeValue = `${FieldActionType}`;

export type ResourceStatusLabel = (typeof RESOURCE_STATUS)[number];
export type ResourceStatusLabelColor =
  | "nectar"
  | "red"
  | "orange"
  | "blue"
  | "green";
