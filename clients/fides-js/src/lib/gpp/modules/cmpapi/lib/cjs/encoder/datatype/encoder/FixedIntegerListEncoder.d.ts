export declare class FixedIntegerListEncoder {
    static encode(value: number[], elementBitStringLength: number, numElements: number): string;
    static decode(bitString: string, elementBitStringLength: number, numElements: number): number[];
}
