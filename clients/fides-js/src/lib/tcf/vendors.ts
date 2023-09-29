import { GVLJson, TCFVendorRecord } from "./types";

export const vendorIsGvl = (
  vendor: Pick<TCFVendorRecord, "id">,
  gvl: GVLJson | undefined
) => {
  if (!gvl) {
    return undefined;
  }
  return gvl.vendors[vendor.id];
};
