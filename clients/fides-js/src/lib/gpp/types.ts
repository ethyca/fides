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

export enum GPPSections {
  TCFEUV2 = "tcfeuv2",
  TCFCAV1 = "tcfcav1",
  USNAT = "usnat",
  USCA = "usca",
  USVA = "usva",
  USCO = "usco",
  USUT = "usut",
  USCT = "usct",
}

export enum GPPUSApproach {
  NATIONAL = "national",
  STATE = "state",
}

export type GPPSettings = {
  enabled?: boolean;
  regions?: Array<GPPSections>;
  /**
   * National ('national') or state-by-state ('state') approach. Only required if regions includes US.
   */
  us_approach?: GPPUSApproach;
  /**
   * List of US states. Only required if using a state-by-state approach.
   */
  us_states?: Array<string>;
};
