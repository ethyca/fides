import type { PingData, EventData } from "@iabgpp/cmpapi";

export type GppCallback = (
  event: PingData | EventData | boolean | null,
  success: boolean
) => void;

export type GppFunction = (
  command: string,
  callback: GppCallback,
  parameter?: number | string,
  version?: string
) => void;
