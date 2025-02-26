import { FIDES_SEPARATOR } from "./constants";
import { VendorSources } from "./vendors";

export const decodeFidesString = (fidesString: string) => {
  const split = fidesString.split(FIDES_SEPARATOR);
  if (split.length === 1) {
    return { tc: split[0], ac: "" };
  }
  if (split.length >= 2) {
    const [tc, ac] = split;
    if (tc === "") {
      return { tc: "", ac: "" };
    }
    return { tc, ac };
  }
  return { tc: "", ac: "" };
};

/**
 * Given an AC string, return a list of its ids, encoded
 *
 * @example
 * // returns [gacp.1, gacp.2, gacp.3]
 * idsFromAcString("1~1.2.3")
 */
export const idsFromAcString = (acString: string) => {
  const isValidAc = /\d~/;
  if (!isValidAc.test(acString)) {
    fidesDebugger(`Received invalid AC string ${acString}, returning no ids`);
    return [];
  }
  const split = acString.split("~");
  if (split.length !== 2) {
    return [];
  }

  const ids = split[1].split(".");
  if (ids.length === 1 && ids[0] === "") {
    return [];
  }
  return ids.map((id) => `${VendorSources.AC}.${id}`);
};
