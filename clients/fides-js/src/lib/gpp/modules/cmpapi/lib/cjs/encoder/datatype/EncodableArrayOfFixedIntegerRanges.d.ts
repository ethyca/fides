import { AbstractEncodableBitStringDataType } from "./AbstractEncodableBitStringDataType.js";
import { RangeEntry } from "./RangeEntry.js";
export declare class EncodableArrayOfFixedIntegerRanges extends AbstractEncodableBitStringDataType<RangeEntry[]> {
    private keyBitStringLength;
    private typeBitStringLength;
    constructor(keyBitStringLength: number, typeBitStringLength: number, value?: RangeEntry[], hardFailIfMissing?: boolean);
    encode(): string;
    decode(bitString: string): void;
    substring(bitString: string, fromIndex: number): string;
}
