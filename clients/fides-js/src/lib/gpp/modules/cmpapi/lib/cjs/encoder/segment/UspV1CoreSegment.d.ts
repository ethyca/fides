import { GenericFields } from "../field/GenericFields.js";
import { AbstractLazilyEncodableSegment } from "./AbstractLazilyEncodableSegment.js";
export declare class UspV1CoreSegment extends AbstractLazilyEncodableSegment<GenericFields> {
    constructor(encodedString?: string);
    getFieldNames(): string[];
    protected initializeFields(): GenericFields;
    protected encodeSegment(fields: GenericFields): string;
    protected decodeSegment(encodedString: string, fields: GenericFields): void;
}
