import { AbstractEncodableBitStringDataType } from "./AbstractEncodableBitStringDataType.js";
export declare class EncodableFixedString extends AbstractEncodableBitStringDataType<string> {
    private stringLength;
    constructor(stringLength: number, value: string, hardFailIfMissing?: boolean);
    encode(): string;
    decode(bitString: string): void;
    substring(bitString: string, fromIndex: number): string;
}
