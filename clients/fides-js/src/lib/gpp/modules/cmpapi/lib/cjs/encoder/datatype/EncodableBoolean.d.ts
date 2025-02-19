import { AbstractEncodableBitStringDataType } from "./AbstractEncodableBitStringDataType.js";
export declare class EncodableBoolean extends AbstractEncodableBitStringDataType<boolean> {
    constructor(value: boolean, hardFailIfMissing?: boolean);
    encode(): string;
    decode(bitString: string): void;
    substring(bitString: string, fromIndex: number): string;
}
