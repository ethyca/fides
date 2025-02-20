import { Fields } from "../field/Fields.js";
import { EncodableSegment } from "./EncodableSegment.js";
export declare abstract class AbstractLazilyEncodableSegment<T extends Fields<any>> implements EncodableSegment {
    protected fields: T;
    private encodedString;
    private dirty;
    private decoded;
    constructor();
    protected abstract initializeFields(): T;
    protected abstract encodeSegment(fields: T): string;
    protected abstract decodeSegment(encodedString: string, Fields: T): void;
    abstract getFieldNames(): string[];
    validate(): void;
    hasField(fieldName: string): boolean;
    getFieldValue(fieldName: string): any;
    setFieldValue(fieldName: string, value: any): void;
    toObj(): any;
    encode(): string;
    decode(encodedString: string): void;
}
