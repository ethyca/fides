import { UsCa, UsCo, UsCt, UsNat, UsUt, UsVa } from "@iabgpp/cmpapi";

import { GPPSection } from "./types";

export const FIDES_REGION_TO_GPP_SECTION: Record<string, GPPSection> = {
  us: { name: UsNat.NAME, id: UsNat.ID, prefix: "usnat" },
  us_ca: { name: UsCa.NAME, id: UsCa.ID, prefix: "usca" },
  us_ct: { name: UsCt.NAME, id: UsCt.ID, prefix: "usct" },
  us_co: { name: UsCo.NAME, id: UsCo.ID, prefix: "usco" },
  us_ut: { name: UsUt.NAME, id: UsUt.ID, prefix: "usut" },
  us_va: { name: UsVa.NAME, id: UsVa.ID, prefix: "usva" },
  // DEFER: Iowa isn't part of the GPP spec yet
};
