import { DataType } from "../datatype/DataType.js";
import { Fields } from "./Fields.js";
export declare class GenericFields implements Fields<DataType<any>> {
    private fields;
    containsKey(key: string): boolean;
    put(key: string, value: DataType<any>): void;
    get(key: string): DataType<any>;
    getAll(): Map<string, DataType<any>>;
    reset(fields: Fields<DataType<any>>): void;
}
