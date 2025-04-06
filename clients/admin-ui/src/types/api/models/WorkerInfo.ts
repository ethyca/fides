/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { TaskDetails } from "./TaskDetails";

export type WorkerInfo = {
  active_task?: TaskDetails | null;
  reserved_tasks?: Array<TaskDetails>;
  registered_tasks?: Array<string>;
};
