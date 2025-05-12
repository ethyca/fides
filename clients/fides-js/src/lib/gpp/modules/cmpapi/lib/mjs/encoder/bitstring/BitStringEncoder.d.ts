import { EncodableBitStringFields } from "../field/EncodableBitStringFields.js";
export declare class BitStringEncoder {
    private static instance;
    private constructor();
    static getInstance(): BitStringEncoder;
    encode(fields: EncodableBitStringFields, fieldNames: string[]): string;
    decode(bitString: string, fieldNames: string[], fields: EncodableBitStringFields): void;
}
