import type { Key } from "antd/es/table/interface";

// Types
export type CheckedKeysType = Key[] | { checked: Key[]; halfChecked: Key[] };
export type ConsentMechanism = "opt-in" | "opt-out";

export interface TreeDataNode {
  title: string;
  key: string;
  disabled?: boolean;
  children?: TreeDataNode[];
}
