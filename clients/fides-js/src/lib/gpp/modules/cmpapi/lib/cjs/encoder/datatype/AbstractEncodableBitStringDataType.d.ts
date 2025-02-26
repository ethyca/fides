import { EncodableDataType } from "./EncodableDataType.js";
import { Predicate } from "./validate/Predicate.js";
export declare abstract class AbstractEncodableBitStringDataType<T> implements EncodableDataType<T> {
    protected hardFailIfMissing: boolean;
    protected validator: Predicate<T>;
    protected value: T;
    constructor(hardFailIfMising?: boolean);
    withValidator(validator: Predicate<T>): AbstractEncodableBitStringDataType<T>;
    hasValue(): boolean;
    getValue(): T;
    setValue(value: T): void;
    getHardFailIfMissing(): boolean;
    abstract encode(): string;
    abstract decode(bitString: string): void;
    abstract substring(bitString: string, fromIndex: number): string;
}
