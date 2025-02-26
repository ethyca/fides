/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { DataSubjectRightsEnum } from "./DataSubjectRightsEnum";
import type { IncludeExcludeEnum } from "./IncludeExcludeEnum";

/**
 * The DataSubjectRights resource model.
 *
 * Includes a strategy and optionally a
 * list of data subject rights to apply
 * via the set strategy.
 */
export type DataSubjectRights = {
  /**
   * Defines the strategy used when mapping data rights to a data subject.
   */
  strategy: IncludeExcludeEnum;
  /**
   * A list of valid data subject rights to be used when applying data rights to a data subject via a strategy.
   */
  values?: Array<DataSubjectRightsEnum> | null;
};
