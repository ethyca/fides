import { AntTreeDataNode as TreeDataNode } from "fidesui";

import {
  ConfidenceBucket,
  Database,
  DatastoreStagedResource,
  Field,
  Schema,
  Table,
  TreeResourceChangeIndicator,
} from "~/types/api";
import { FieldActionType } from "~/types/api/models/FieldActionType";

export type MonitorResource =
  | DatastoreStagedResource
  | Database
  | Schema
  | Table
  | Field;

/**
 * Extend TreeDataNode to include the update status from the API response
 * and force the title to be a string since we use a custom title renderer
 */
export interface CustomTreeDataNode extends TreeDataNode {
  title?: string | null;
  status?: TreeResourceChangeIndicator | null;
  children?: CustomTreeDataNode[];
  classifyable?: boolean;
}

export type FieldActionTypeValue = `${FieldActionType}`;

interface MonitorFieldQueryParameters {
  staged_resource_urn?: Array<string>;
  search?: string;
  diff_status?: Array<DiffStatus>;
  confidence_bucket?: Array<ConfidenceBucket>;
  data_category?: Array<string>;
}

export interface MonitorFieldParameters {
  path: {
    monitor_config_id: string;
  };
  query: MonitorFieldQueryParameters;
}

export type TreeNodeAction = {
  label: string;
  /** TODO: should be generically typed * */
  callback: (key: Key, node: CustomTreeDataNode) => void;
  disabled?: (node: CustomTreeDataNode) => Promise<boolean>;
};
