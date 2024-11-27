/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { DataSubjectRights } from "./DataSubjectRights";

export type DataSubjectCreate = {
  name?: string | null;
  description: string;
  active?: boolean;
  fides_key?: string | null;
  is_default?: boolean;
  tags?: Array<string> | null;
  organization_fides_key?: string | null;
  rights?: DataSubjectRights | null;
  automated_decisions_or_profiling?: boolean | null;
};
