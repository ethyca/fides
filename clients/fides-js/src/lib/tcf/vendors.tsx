import { TCFVendorRecord } from "./types";
import GVL_JSON from "./gvl.json";

const GVL_VENDOR_IDS = Object.keys(GVL_JSON.vendors);

export const vendorIsGvl = (vendor: TCFVendorRecord) =>
  GVL_VENDOR_IDS.indexOf(vendor.id) !== -1;
