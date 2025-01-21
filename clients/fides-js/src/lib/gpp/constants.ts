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
  UsTn,
  UsTx,
  UsUt,
  UsVa,
} from "@iabgpp/cmpapi";

import { GPPSection } from "./types";

export const FIDES_REGION_TO_GPP_SECTION: Record<string, GPPSection> = {
  us: { name: UsNat.NAME, id: UsNat.ID, prefix: "usnat" },
  us_ca: { name: UsCa.NAME, id: UsCa.ID, prefix: "usca" },
  us_ct: { name: UsCt.NAME, id: UsCt.ID, prefix: "usct" },
  us_co: { name: UsCo.NAME, id: UsCo.ID, prefix: "usco" },
  us_ut: { name: UsUt.NAME, id: UsUt.ID, prefix: "usut" },
  us_va: { name: UsVa.NAME, id: UsVa.ID, prefix: "usva" },
  us_de: { name: UsDe.NAME, id: UsDe.ID, prefix: "usde" },
  us_fl: { name: UsFl.NAME, id: UsFl.ID, prefix: "usfl" },
  us_ia: { name: UsIa.NAME, id: UsIa.ID, prefix: "usia" },
  us_mt: { name: UsMt.NAME, id: UsMt.ID, prefix: "usmt" },
  us_ne: { name: UsNe.NAME, id: UsNe.ID, prefix: "usne" },
  us_nh: { name: UsNh.NAME, id: UsNh.ID, prefix: "usnh" },
  us_nj: { name: UsNj.NAME, id: UsNj.ID, prefix: "usnj" },
  us_tn: { name: UsTn.NAME, id: UsTn.ID, prefix: "ustn" },
  us_tx: { name: UsTx.NAME, id: UsTx.ID, prefix: "ustx" },
};
