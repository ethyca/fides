export declare class RangeEntry {
    private key;
    private type;
    private ids;
    constructor(key: number, type: number, ids: number[]);
    getKey(): number;
    setKey(key: number): void;
    getType(): number;
    setType(type: number): void;
    getIds(): number[];
    setIds(ids: number[]): void;
}
