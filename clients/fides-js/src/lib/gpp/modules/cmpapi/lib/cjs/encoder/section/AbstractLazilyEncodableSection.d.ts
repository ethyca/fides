import { EncodableSegment } from "../segment/EncodableSegment.js";
import { EncodableSection } from "./EncodableSection.js";
export declare abstract class AbstractLazilyEncodableSection implements EncodableSection {
    abstract getId(): number;
    abstract getName(): string;
    private segments;
    private encodedString;
    private dirty;
    private decoded;
    constructor();
    protected abstract initializeSegments(): EncodableSegment[];
    protected abstract encodeSection(segments: EncodableSegment[]): string;
    protected abstract decodeSection(encodedString: string): EncodableSegment[];
    hasField(fieldName: string): boolean;
    getFieldValue(fieldName: string): any;
    setFieldValue(fieldName: string, value: any): void;
    toObj(): any;
    encode(): string;
    decode(encodedString: string): void;
    setIsDirty(status: boolean): void;
}
