import { DataType } from "./DataType.js";
export interface EncodableDataType<T> extends DataType<T> {
    encode(): string;
    decode(str: string): void;
}
