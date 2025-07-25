import type { EventData, PingData } from "@iabgpp/cmpapi";

import {
  PrivacyNoticeWithPreference,
  UserConsentPreference,
} from "../consent-types";
import { GPPUSApproach } from "./constants";

export interface GppCallback {
  (event: PingData | EventData | boolean | null, success: boolean): void;
}

export type GppFunction = (
  command: string,
  callback: GppCallback,
  parameter?: number | string,
  version?: string,
) => void;

export interface GPPSettings {
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
  /**
   * Whether the GPP CMP API is required for the experience
   */
  cmp_api_required?: boolean;
}

export interface GPPMechanismMapping {
  field: string;
  not_available: string;
  opt_out: string;
  not_opt_out: string;
}

export interface GPPFieldMapping {
  region: string;
  notice?: Array<string>;
  mechanism?: Array<GPPMechanismMapping>;
}

export interface GPPSection {
  name: string;
  id: number;
}

export type NoticeConsent = Record<string, boolean | UserConsentPreference>;
export type PrivacyNotice = PrivacyNoticeWithPreference;

// Generic privacy experience type for GPP use
export interface GPPPrivacyExperience {
  region: string;
  gpp_settings?: GPPSettings;
  privacy_notices?: Array<PrivacyNotice>;
}
