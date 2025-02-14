import { CompressedBase64UrlEncoder } from "../base64/CompressedBase64UrlEncoder.js";
import { BitStringEncoder } from "../bitstring/BitStringEncoder.js";
import { EncodableBoolean } from "../datatype/EncodableBoolean.js";
import { EncodableFixedInteger } from "../datatype/EncodableFixedInteger.js";
import { DecodingError } from "../error/DecodingError.js";
import { EncodableBitStringFields } from "../field/EncodableBitStringFields.js";
import { USOR_GPC_SEGMENT_FIELD_NAMES } from "../field/UsOrField.js";
import { UsOrField } from "../field/UsOrField.js";
import { AbstractLazilyEncodableSegment } from "./AbstractLazilyEncodableSegment.js";
export class UsOrGpcSegment extends AbstractLazilyEncodableSegment {
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
        return USOR_GPC_SEGMENT_FIELD_NAMES;
    }
    // overriden
    initializeFields() {
        let fields = new EncodableBitStringFields();
        fields.put(UsOrField.GPC_SEGMENT_TYPE.toString(), new EncodableFixedInteger(2, 1));
        fields.put(UsOrField.GPC_SEGMENT_INCLUDED.toString(), new EncodableBoolean(true));
        fields.put(UsOrField.GPC.toString(), new EncodableBoolean(false));
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
            throw new DecodingError("Unable to decode UsOrGpcSegment '" + encodedString + "'");
        }
    }
}
