/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ClassificationStatus } from "./ClassificationStatus";
import type { ClassifyDataFlow } from "./ClassifyDataFlow";

export type ClassifySystem = {
  fides_key: string;
  name: string;
  status: ClassificationStatus;
  egress: Array<ClassifyDataFlow>;
  ingress: Array<ClassifyDataFlow>;
};
