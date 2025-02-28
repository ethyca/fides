import {
  TcfEuV2,
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

export const fidesSupportedGPPApis = [
  TcfEuV2,
  UsNat,
  UsCa,
  UsCo,
  UsCt,
  UsUt,
  UsVa,
  UsDe,
  UsFl,
  UsIa,
  UsMt,
  UsNe,
  UsNh,
  UsNj,
  UsTn,
  UsTx,
];

export const FIDES_US_REGION_TO_GPP_SECTION: Record<string, GPPSection> =
  Object.fromEntries(
    fidesSupportedGPPApis
      .filter((api) => api.NAME !== TcfEuV2.NAME) // Exclude TCF since it's not US region-based
      .map((api) => {
        // Convert section name to Fides region format (e.g., "uspv1_ct" -> "us_ct")
        const regionKey =
          api.NAME === UsNat.NAME
            ? "us"
            : `us_${api.NAME.slice(-2).toLowerCase()}`;

        return [regionKey, { name: api.NAME, id: api.ID }];
      }),
  );
