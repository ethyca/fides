import { FidesBase, FidesKey } from "../common/fides-types";

export interface DataCategory extends FidesBase {
  parent_key: FidesKey | null;
}
