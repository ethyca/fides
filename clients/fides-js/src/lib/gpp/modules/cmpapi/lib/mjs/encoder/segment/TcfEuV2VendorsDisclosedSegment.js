import { TraditionalBase64UrlEncoder } from "../base64/TraditionalBase64UrlEncoder.js";
import { BitStringEncoder } from "../bitstring/BitStringEncoder.js";
import { EncodableFixedInteger } from "../datatype/EncodableFixedInteger.js";
import { EncodableOptimizedFixedRange } from "../datatype/EncodableOptimizedFixedRange.js";
import { DecodingError } from "../error/DecodingError.js";
import { EncodableBitStringFields } from "../field/EncodableBitStringFields.js";
import { TCFEUV2_VENDORS_DISCLOSED_SEGMENT_FIELD_NAMES } from "../field/TcfEuV2Field.js";
import { TcfEuV2Field } from "../field/TcfEuV2Field.js";
import { AbstractLazilyEncodableSegment } from "./AbstractLazilyEncodableSegment.js";
export class TcfEuV2VendorsDisclosedSegment extends AbstractLazilyEncodableSegment {
    base64UrlEncoder = TraditionalBase64UrlEncoder.getInstance();
    bitStringEncoder = BitStringEncoder.getInstance();
    constructor(encodedString) {
        super();
        if (encodedString) {
            this.decode(encodedString);
        }
    }
    // overriden
    getFieldNames() {
        return TCFEUV2_VENDORS_DISCLOSED_SEGMENT_FIELD_NAMES;
    }
    // overriden
    initializeFields() {
        let fields = new EncodableBitStringFields();
        fields.put(TcfEuV2Field.VENDORS_DISCLOSED_SEGMENT_TYPE.toString(), new EncodableFixedInteger(3, 1));
        fields.put(TcfEuV2Field.VENDORS_DISCLOSED.toString(), new EncodableOptimizedFixedRange([]));
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
            throw new DecodingError("Unable to decode TcfEuV2VendorsDisclosedSegment '" + encodedString + "'");
        }
    }
}
