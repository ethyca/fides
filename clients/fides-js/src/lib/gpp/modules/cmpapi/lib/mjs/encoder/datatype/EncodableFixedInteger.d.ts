import { AbstractEncodableBitStringDataType } from "./AbstractEncodableBitStringDataType.js";
export declare class EncodableFixedInteger extends AbstractEncodableBitStringDataType<number> {
    private bitStringLength;
    constructor(bitStringLength: number, value: number, hardFailIfMissing?: boolean);
    encode(): string;
    decode(bitString: string): void;
    substring(bitString: string, fromIndex: number): string;
}
