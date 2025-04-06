import { AbstractEncodableBitStringDataType } from "./AbstractEncodableBitStringDataType.js";
export declare class EncodableFixedBitfield extends AbstractEncodableBitStringDataType<boolean[]> {
    private numElements;
    constructor(value: boolean[], hardFailIfMissing?: boolean);
    encode(): string;
    decode(bitString: string): void;
    substring(bitString: string, fromIndex: number): string;
    getValue(): boolean[];
    setValue(value: boolean[]): void;
}
