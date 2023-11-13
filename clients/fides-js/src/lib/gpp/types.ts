import type { PingData, EventData } from "@iabgpp/cmpapi";

export type GppFunction = (
  command: string,
  callback: (event: PingData | EventData, success: boolean) => void,
  parameter?: number | string,
  version?: string
) => void;
