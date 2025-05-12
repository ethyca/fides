import { CompressedBase64UrlEncoder } from "../base64/CompressedBase64UrlEncoder.js";
import { BitStringEncoder } from "../bitstring/BitStringEncoder.js";
import { EncodableFibonacciIntegerRange } from "../datatype/EncodableFibonacciIntegerRange.js";
import { EncodableFixedInteger } from "../datatype/EncodableFixedInteger.js";
import { DecodingError } from "../error/DecodingError.js";
import { EncodableBitStringFields } from "../field/EncodableBitStringFields.js";
import { HEADER_CORE_SEGMENT_FIELD_NAMES } from "../field/HeaderV1Field.js";
import { HeaderV1Field } from "../field/HeaderV1Field.js";
import { HeaderV1 } from "../section/HeaderV1.js";
import { AbstractLazilyEncodableSegment } from "./AbstractLazilyEncodableSegment.js";
export class HeaderV1CoreSegment extends AbstractLazilyEncodableSegment {
    base64UrlEncoder = CompressedBase64UrlEncoder.getInstance();
    bitStringEncoder = BitStringEncoder.getInstance();
    constructor(encodedString) {
        super();
        if (encodedString) {
            this.decode(encodedString);
        }
    }
    // overriden
    getFieldNames() {
        return HEADER_CORE_SEGMENT_FIELD_NAMES;
    }
    // overriden
    initializeFields() {
        let fields = new EncodableBitStringFields();
        fields.put(HeaderV1Field.ID.toString(), new EncodableFixedInteger(6, HeaderV1.ID));
        fields.put(HeaderV1Field.VERSION.toString(), new EncodableFixedInteger(6, HeaderV1.VERSION));
        fields.put(HeaderV1Field.SECTION_IDS.toString(), new EncodableFibonacciIntegerRange([]));
        return fields;
    }
    // overriden
    encodeSegment(fields) {
        let bitString = this.bitStringEncoder.encode(fields, this.getFieldNames());
        let encodedString = this.base64UrlEncoder.encode(bitString);
        return encodedString;
    }
    // overriden
    decodeSegment(encodedString, fields) {
        if (encodedString == null || encodedString.length === 0) {
            this.fields.reset(fields);
        }
        try {
            let bitString = this.base64UrlEncoder.decode(encodedString);
            this.bitStringEncoder.decode(bitString, this.getFieldNames(), fields);
        }
        catch (e) {
            throw new DecodingError("Unable to decode HeaderV1CoreSegment '" + encodedString + "'");
        }
    }
}
