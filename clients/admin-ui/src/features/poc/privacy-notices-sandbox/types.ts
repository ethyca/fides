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

export interface PreferenceItem {
  notice_key: string;
  value: "opt_in" | "opt_out";
  notice_history_id: string;
  meta: {
    timestamp: string;
  };
}
