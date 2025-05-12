import { DataType } from "./DataType.js";
import { Predicate } from "./validate/Predicate.js";
export declare class UnencodableInteger implements DataType<number> {
    protected validator: Predicate<number>;
    private value;
    constructor(value: number, validator?: Predicate<number>);
    hasValue(): boolean;
    getValue(): number;
    setValue(value: number): void;
}
