import { IntMap } from './IntMap.js';
import { Vendor } from './Vendor.js';
import { Declarations } from './Declarations.js';
export interface VendorList extends Declarations {
    lastUpdated: string | Date;
    gvlSpecificationVersion: number;
    vendorListVersion: number;
    tcfPolicyVersion: number;
    vendors: IntMap<Vendor>;
}
