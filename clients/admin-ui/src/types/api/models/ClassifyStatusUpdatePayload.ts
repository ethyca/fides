/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ClassificationStatus } from "./ClassificationStatus";

export type ClassifyStatusUpdatePayload = {
  dataset_fides_key: string;
  status: ClassificationStatus;
};
