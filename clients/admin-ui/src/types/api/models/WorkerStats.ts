/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { QueueInfo } from "./QueueInfo";
import type { WorkerInfo } from "./WorkerInfo";

export type WorkerStats = {
  queues: Record<string, QueueInfo>;
  workers: Record<string, WorkerInfo>;
};
