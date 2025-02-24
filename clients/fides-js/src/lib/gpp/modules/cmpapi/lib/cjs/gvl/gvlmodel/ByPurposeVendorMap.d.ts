export interface ByPurposeVendorMap {
    [purposeId: string]: {
        legInt: Set<number>;
        impCons: Set<number>;
        consent: Set<number>;
        flexible: Set<number>;
    };
}
