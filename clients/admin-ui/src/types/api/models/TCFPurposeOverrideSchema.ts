/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { TCFLegalBasisEnum } from "./TCFLegalBasisEnum";

/**
 * TCF Purpose Override Schema
 */
export type TCFPurposeOverrideSchema = {
  purpose: number;
  is_included?: boolean | null;
  required_legal_basis?: TCFLegalBasisEnum | null;
};
