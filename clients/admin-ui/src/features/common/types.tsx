import { RTKErrorResult } from "~/types/errors";

export interface TreeNode {
  label: string;
  value: string;
  children: TreeNode[] | [];
}

export type RTKResult<T> = Promise<
  | {
      data: T;
    }
  | { error: RTKErrorResult["error"] }
>;
