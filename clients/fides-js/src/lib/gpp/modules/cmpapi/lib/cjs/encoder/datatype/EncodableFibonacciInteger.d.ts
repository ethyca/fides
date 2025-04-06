import { AbstractEncodableBitStringDataType } from "./AbstractEncodableBitStringDataType.js";
export declare class EncodableFibonacciInteger extends AbstractEncodableBitStringDataType<number> {
    constructor(value: number, hardFailIfMissing?: boolean);
    encode(): string;
    decode(bitString: string): void;
    substring(bitString: string, fromIndex: number): string;
}
