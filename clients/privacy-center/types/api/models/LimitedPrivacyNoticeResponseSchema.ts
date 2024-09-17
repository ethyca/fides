/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConsentMechanism } from "./ConsentMechanism";
import type { PrivacyNoticeFramework } from "./PrivacyNoticeFramework";
import type { PrivacyNoticeRegion } from "./PrivacyNoticeRegion";

/**
 * Limited Privacy Notice Schema for List View in Admin UI
 * For performance, only returns a subset of available fields for this view.
 */
export type LimitedPrivacyNoticeResponseSchema = {
  id: string;
  name: string;
  notice_key: string;
  data_uses: Array<string>;
  consent_mechanism: ConsentMechanism;
  /**
   * A property calculated by observing which Experiences have linked this Notice
   */
  configured_regions?: Array<PrivacyNoticeRegion>;
  systems_applicable?: boolean;
  disabled: boolean;
  framework?: PrivacyNoticeFramework | null;
  children?: Array<LimitedPrivacyNoticeResponseSchema>;
};
