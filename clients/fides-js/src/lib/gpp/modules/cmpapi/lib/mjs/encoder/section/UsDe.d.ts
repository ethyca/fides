import { EncodableSegment } from "../segment/EncodableSegment.js";
import { AbstractLazilyEncodableSection } from "./AbstractLazilyEncodableSection.js";
export declare class UsDe extends AbstractLazilyEncodableSection {
    static readonly ID = 17;
    static readonly VERSION = 1;
    static readonly NAME = "usde";
    constructor(encodedString?: string);
    getId(): number;
    getName(): string;
    getVersion(): number;
    protected initializeSegments(): EncodableSegment[];
    protected decodeSection(encodedString: string): EncodableSegment[];
    protected encodeSection(segments: EncodableSegment[]): string;
}
