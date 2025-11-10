/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConsentMetaResponse } from "./ConsentMetaResponse";
import type { ConsentPreferenceResponse } from "./ConsentPreferenceResponse";
import type { ConsentScopeResponse } from "./ConsentScopeResponse";
import type { fidesplus__v3__schemas__identity__Identity } from "./fidesplus__v3__schemas__identity__Identity";

/**
 * Unified consent v3 schema with server-generated fields (ID, created_at, etc.).
 */
export type ConsentResponse = {
  identity: fidesplus__v3__schemas__identity__Identity;
  scope?: ConsentScopeResponse | null;
  meta: ConsentMetaResponse;
  preferences: Array<ConsentPreferenceResponse>;
};
