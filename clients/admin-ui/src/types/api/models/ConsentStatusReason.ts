/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConsentMechanism } from "./ConsentMechanism";
import type { LoadingContext } from "./LoadingContext";

/**
 * TypedDict for storing details relevant to the consent status for a given asset
 */
export type ConsentStatusReason = {
  notice_key: string;
  mechanism: ConsentMechanism;
  loading_context: LoadingContext;
};
