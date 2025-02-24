import { AbstractEncodableBitStringDataType } from "../datatype/AbstractEncodableBitStringDataType.js";
import { Fields } from "./Fields.js";
export declare class EncodableBitStringFields implements Fields<AbstractEncodableBitStringDataType<any>> {
    private fields;
    containsKey(key: string): boolean;
    put(key: string, value: AbstractEncodableBitStringDataType<any>): void;
    get(key: string): AbstractEncodableBitStringDataType<any>;
    getAll(): Map<string, AbstractEncodableBitStringDataType<any>>;
    reset(fields: Fields<AbstractEncodableBitStringDataType<any>>): void;
}
