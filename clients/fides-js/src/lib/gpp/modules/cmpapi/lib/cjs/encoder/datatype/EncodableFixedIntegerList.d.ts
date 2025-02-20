import { AbstractEncodableBitStringDataType } from "./AbstractEncodableBitStringDataType.js";
export declare class EncodableFixedIntegerList extends AbstractEncodableBitStringDataType<number[]> {
    private elementBitStringLength;
    private numElements;
    constructor(elementBitStringLength: number, value: number[], hardFailIfMissing?: boolean);
    encode(): string;
    decode(bitString: string): void;
    substring(bitString: string, fromIndex: number): string;
    getValue(): number[];
    setValue(value: number[]): void;
}
