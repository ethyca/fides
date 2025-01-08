import type { EventData, PingData } from "@iabgpp/cmpapi";

export type GppCallback = (
  event: PingData | EventData | boolean | null,
  success: boolean,
) => void;

export type GppFunction = (
  command: string,
  callback: GppCallback,
  parameter?: number | string,
  version?: string,
) => void;

export enum GPPUSApproach {
  NATIONAL = "national",
  STATE = "state",
  ALL = "all",
}

export type GPPSettings = {
  enabled?: boolean;
  /**
   * National ('national') or state-by-state ('state') approach. Only required if regions includes US.
   */
  us_approach?: GPPUSApproach;
  /**
   * List of US states. Only required if using a state-by-state approach.
   */
  us_states?: Array<string>;
  /**
   * Whether MSPA service provider mode is enabled
   */
  mspa_service_provider_mode?: boolean;
  /**
   * Whether MSPA opt out option mode is enabled
   */
  mspa_opt_out_option_mode?: boolean;
  /**
   * Whether all transactions are MSPA covered
   */
  mspa_covered_transactions?: boolean;
  /**
   * Whether TC string should be included as a section in GPP
   */
  enable_tcfeu_string?: boolean;
};

export type GPPMechanismMapping = {
  field: string;
  not_available: string;
  opt_out: string;
  not_opt_out: string;
};

export type GPPFieldMapping = {
  region: string;
  notice?: Array<string>;
  mechanism?: Array<GPPMechanismMapping>;
};

export type GPPSection = {
  name: string;
  id: number;
  prefix?: string;
};
