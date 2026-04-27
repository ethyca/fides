export interface QueueStats {
  queue_name: string;
  available: number;
  delayed: number;
  in_flight: number;
}

export interface QueueMonitorResponse {
  sqs_enabled: boolean;
  queues: QueueStats[];
}
