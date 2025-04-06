export interface DataType<T> {
    hasValue(): boolean;
    getValue(): T;
    setValue(value: T): void;
}
