import { AbstractEncodableBitStringDataType } from "./AbstractEncodableBitStringDataType.js";
export declare class EncodableFlexibleBitfield extends AbstractEncodableBitStringDataType<boolean[]> {
    private getLength;
    constructor(getLength: () => number, value?: boolean[], hardFailIfMissing?: boolean);
    encode(): string;
    decode(bitString: string): void;
    substring(bitString: string, fromIndex: number): string;
    getValue(): boolean[];
    setValue(value: boolean[]): void;
}
