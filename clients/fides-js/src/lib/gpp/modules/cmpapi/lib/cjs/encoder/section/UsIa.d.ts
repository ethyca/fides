import { EncodableSegment } from "../segment/EncodableSegment.js";
import { AbstractLazilyEncodableSection } from "./AbstractLazilyEncodableSection.js";
export declare class UsIa extends AbstractLazilyEncodableSection {
    static readonly ID = 18;
    static readonly VERSION = 1;
    static readonly NAME = "usia";
    constructor(encodedString?: string);
    getId(): number;
    getName(): string;
    getVersion(): number;
    protected initializeSegments(): EncodableSegment[];
    protected decodeSection(encodedString: string): EncodableSegment[];
    protected encodeSection(segments: EncodableSegment[]): string;
}
