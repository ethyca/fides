import { EncodableSegment } from "../segment/EncodableSegment.js";
import { AbstractLazilyEncodableSection } from "./AbstractLazilyEncodableSection.js";
export declare class TcfEuV2 extends AbstractLazilyEncodableSection {
    static readonly ID = 2;
    static readonly VERSION = 2;
    static readonly NAME = "tcfeuv2";
    constructor(encodedString?: string);
    getId(): number;
    getName(): string;
    getVersion(): number;
    protected initializeSegments(): EncodableSegment[];
    protected decodeSection(encodedString: string): EncodableSegment[];
    protected encodeSection(segments: EncodableSegment[]): string;
    setFieldValue(fieldName: string, value: any): void;
}
