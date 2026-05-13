/* istanbul ignore file */
/* tslint:disable */

import type { ClassificationStatus } from "./ClassificationStatus";
import type { ClassifyCollection } from "./ClassifyCollection";

export type ClassifyDataset = {
  fides_key: string;
  name: string;
  status: ClassificationStatus;
  collections: Array<ClassifyCollection>;
};
