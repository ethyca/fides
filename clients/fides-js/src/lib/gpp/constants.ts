import {
  UsCa,
  UsCo,
  UsCt,
  UsDe,
  UsFl,
  UsIa,
  UsMt,
  UsNat,
  UsNe,
  UsNh,
  UsNj,
  UsOr,
  UsTn,
  UsTx,
  UsUt,
  UsVa,
} from "@iabgpp/cmpapi";

import { GPPSection } from "./types";

export const CMP_VERSION = 1;

/**
 * This is the mapping of Fides experience region codes to GPP sections. This
 * helps determine which GPP section to use for a given experience. It also
 * doubles as a comprehensive list of all GPP RegionAPIs that we support. If a
 * new GPP API is added, it must be added here.
 */
export const FIDES_US_REGION_TO_GPP_SECTION: Record<string, GPPSection> = {
  us: { name: UsNat.NAME, id: UsNat.ID },
  us_ca: { name: UsCa.NAME, id: UsCa.ID },
  us_co: { name: UsCo.NAME, id: UsCo.ID },
  us_ct: { name: UsCt.NAME, id: UsCt.ID },
  us_ut: { name: UsUt.NAME, id: UsUt.ID },
  us_va: { name: UsVa.NAME, id: UsVa.ID },
  us_de: { name: UsDe.NAME, id: UsDe.ID },
  us_fl: { name: UsFl.NAME, id: UsFl.ID },
  us_ia: { name: UsIa.NAME, id: UsIa.ID },
  us_mt: { name: UsMt.NAME, id: UsMt.ID },
  us_ne: { name: UsNe.NAME, id: UsNe.ID },
  us_nh: { name: UsNh.NAME, id: UsNh.ID },
  us_nj: { name: UsNj.NAME, id: UsNj.ID },
  us_or: { name: UsOr.NAME, id: UsOr.ID },
  us_tn: { name: UsTn.NAME, id: UsTn.ID },
  us_tx: { name: UsTx.NAME, id: UsTx.ID },
};

/**
 * This is a list of GPP sections that are known to support the GPC subsection.
 * Unfortunately, there's no static way to determine this at build-time, so we
 * have to maintain a hardcoded list.
 *
 * However, our unit tests do dynamically check *all* sections to ensure that
 * this list is accurate and updated whenever the @iabgpp/cmpapi library
 * changes. See us-notices.test.ts for more details.
 */
export const SECTIONS_WITH_GPC_SUBSECTION = [
  UsNat.NAME,
  UsCa.NAME,
  UsCo.NAME,
  UsCt.NAME,
  UsDe.NAME,
  UsIa.NAME,
  UsMt.NAME,
  UsNe.NAME,
  UsNh.NAME,
  UsNj.NAME,
  UsOr.NAME,
  UsTn.NAME,
  UsTx.NAME,
];

export enum GPPUSApproach {
  NATIONAL = "national",
  STATE = "state",
  ALL = "all",
}
