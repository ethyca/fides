import { EncodableSegment } from "../segment/EncodableSegment.js";
import { AbstractLazilyEncodableSection } from "./AbstractLazilyEncodableSection.js";
export declare class TcfCaV1 extends AbstractLazilyEncodableSection {
    static readonly ID = 5;
    static readonly VERSION = 1;
    static readonly NAME = "tcfcav1";
    constructor(encodedString?: string);
    getId(): number;
    getName(): string;
    getVersion(): number;
    protected initializeSegments(): EncodableSegment[];
    protected decodeSection(encodedString: string): EncodableSegment[];
    protected encodeSection(segments: EncodableSegment[]): string;
    setFieldValue(fieldName: string, value: any): void;
}
