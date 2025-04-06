import { DataType } from "./DataType.js";
import { Predicate } from "./validate/Predicate.js";
export declare class UnencodableCharacter implements DataType<string> {
    protected validator: Predicate<string>;
    private value;
    constructor(value: string, validator?: Predicate<string>);
    hasValue(): boolean;
    getValue(): string;
    setValue(value: string): void;
}
