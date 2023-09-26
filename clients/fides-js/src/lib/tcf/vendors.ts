import { GVLJson, TCFVendorRecord } from "./types";

export const vendorIsGvl = (
  vendor: Pick<TCFVendorRecord, "id">,
  gvl: GVLJson | undefined
) => {
  if (!gvl) {
    return false;
  }
  const vendorIds = Object.keys(gvl.vendors);
  return vendorIds.indexOf(vendor.id) !== -1;
};
