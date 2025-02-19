import { AbstractLazilyEncodableSection } from "./AbstractLazilyEncodableSection.js";
import { EncodableSegment } from "../segment/EncodableSegment.js";
export declare class UsCo extends AbstractLazilyEncodableSection {
    static readonly ID = 10;
    static readonly VERSION = 1;
    static readonly NAME = "usco";
    constructor(encodedString?: string);
    getId(): number;
    getName(): string;
    getVersion(): number;
    protected initializeSegments(): EncodableSegment[];
    protected decodeSection(encodedString: string): EncodableSegment[];
    protected encodeSection(segments: EncodableSegment[]): string;
}
