import { AbstractLazilyEncodableSection } from "./AbstractLazilyEncodableSection.js";
import { EncodableSegment } from "../segment/EncodableSegment.js";
export declare class HeaderV1 extends AbstractLazilyEncodableSection {
    static readonly ID = 3;
    static readonly VERSION = 1;
    static readonly NAME = "header";
    constructor(encodedString?: string);
    getId(): number;
    getName(): string;
    getVersion(): number;
    protected initializeSegments(): EncodableSegment[];
    protected decodeSection(encodedString: string): EncodableSegment[];
    protected encodeSection(segments: EncodableSegment[]): string;
}
