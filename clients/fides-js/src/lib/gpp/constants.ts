import {
  UsCaV1,
  UsCoV1,
  UsCtV1,
  UsNatV1,
  UsUtV1,
  UsVaV1,
} from "@iabgpp/cmpapi";

import { GPPSection } from "./types";

export const FIDES_REGION_TO_GPP_SECTION: Record<string, GPPSection> = {
  us: { name: UsNatV1.NAME, id: UsNatV1.ID, prefix: "usnat" },
  us_ca: { name: UsCaV1.NAME, id: UsCaV1.ID, prefix: "usca" },
  us_ct: { name: UsCtV1.NAME, id: UsCtV1.ID, prefix: "usct" },
  us_co: { name: UsCoV1.NAME, id: UsCoV1.ID, prefix: "usco" },
  us_ut: { name: UsUtV1.NAME, id: UsUtV1.ID, prefix: "usut" },
  us_va: { name: UsVaV1.NAME, id: UsVaV1.ID, prefix: "usva" },
  // DEFER: Iowa isn't part of the GPP spec yet
};
