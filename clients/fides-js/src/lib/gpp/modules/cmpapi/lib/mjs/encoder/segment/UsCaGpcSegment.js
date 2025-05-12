import { CompressedBase64UrlEncoder } from "../base64/CompressedBase64UrlEncoder.js";
import { BitStringEncoder } from "../bitstring/BitStringEncoder.js";
import { EncodableBoolean } from "../datatype/EncodableBoolean.js";
import { EncodableFixedInteger } from "../datatype/EncodableFixedInteger.js";
import { DecodingError } from "../error/DecodingError.js";
import { EncodableBitStringFields } from "../field/EncodableBitStringFields.js";
import { USCA_GPC_SEGMENT_FIELD_NAMES } from "../field/UsCaField.js";
import { UsCaField } from "../field/UsCaField.js";
import { AbstractLazilyEncodableSegment } from "./AbstractLazilyEncodableSegment.js";
export class UsCaGpcSegment extends AbstractLazilyEncodableSegment {
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
        return USCA_GPC_SEGMENT_FIELD_NAMES;
    }
    // overriden
    initializeFields() {
        let fields = new EncodableBitStringFields();
        fields.put(UsCaField.GPC_SEGMENT_TYPE.toString(), new EncodableFixedInteger(2, 1));
        fields.put(UsCaField.GPC_SEGMENT_INCLUDED.toString(), new EncodableBoolean(true));
        fields.put(UsCaField.GPC.toString(), new EncodableBoolean(false));
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
            throw new DecodingError("Unable to decode UsCaGpcSegment '" + encodedString + "'");
        }
    }
}
