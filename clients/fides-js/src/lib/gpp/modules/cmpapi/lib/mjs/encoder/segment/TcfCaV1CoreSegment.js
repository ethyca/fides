import { CompressedBase64UrlEncoder } from "../base64/CompressedBase64UrlEncoder.js";
import { BitStringEncoder } from "../bitstring/BitStringEncoder.js";
import { EncodableArrayOfFixedIntegerRanges } from "../datatype/EncodableArrayOfFixedIntegerRanges.js";
import { EncodableBoolean } from "../datatype/EncodableBoolean.js";
import { EncodableDatetime } from "../datatype/EncodableDatetime.js";
import { EncodableFixedBitfield } from "../datatype/EncodableFixedBitfield.js";
import { EncodableFixedInteger } from "../datatype/EncodableFixedInteger.js";
import { EncodableFixedString } from "../datatype/EncodableFixedString.js";
import { EncodableOptimizedFixedRange } from "../datatype/EncodableOptimizedFixedRange.js";
import { DecodingError } from "../error/DecodingError.js";
import { EncodableBitStringFields } from "../field/EncodableBitStringFields.js";
import { TCFCAV1_CORE_SEGMENT_FIELD_NAMES } from "../field/TcfCaV1Field.js";
import { TcfCaV1Field } from "../field/TcfCaV1Field.js";
import { TcfCaV1 } from "../section/TcfCaV1.js";
import { AbstractLazilyEncodableSegment } from "./AbstractLazilyEncodableSegment.js";
export class TcfCaV1CoreSegment extends AbstractLazilyEncodableSegment {
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
        return TCFCAV1_CORE_SEGMENT_FIELD_NAMES;
    }
    // overriden
    initializeFields() {
        let date = new Date();
        let fields = new EncodableBitStringFields();
        fields.put(TcfCaV1Field.VERSION.toString(), new EncodableFixedInteger(6, TcfCaV1.VERSION));
        fields.put(TcfCaV1Field.CREATED.toString(), new EncodableDatetime(date));
        fields.put(TcfCaV1Field.LAST_UPDATED.toString(), new EncodableDatetime(date));
        fields.put(TcfCaV1Field.CMP_ID.toString(), new EncodableFixedInteger(12, 0));
        fields.put(TcfCaV1Field.CMP_VERSION.toString(), new EncodableFixedInteger(12, 0));
        fields.put(TcfCaV1Field.CONSENT_SCREEN.toString(), new EncodableFixedInteger(6, 0));
        fields.put(TcfCaV1Field.CONSENT_LANGUAGE.toString(), new EncodableFixedString(2, "EN"));
        fields.put(TcfCaV1Field.VENDOR_LIST_VERSION.toString(), new EncodableFixedInteger(12, 0));
        fields.put(TcfCaV1Field.TCF_POLICY_VERSION.toString(), new EncodableFixedInteger(6, 2));
        fields.put(TcfCaV1Field.USE_NON_STANDARD_STACKS.toString(), new EncodableBoolean(false));
        fields.put(TcfCaV1Field.SPECIAL_FEATURE_EXPRESS_CONSENT.toString(), new EncodableFixedBitfield([false, false, false, false, false, false, false, false, false, false, false, false]));
        fields.put(TcfCaV1Field.PURPOSES_EXPRESS_CONSENT.toString(), new EncodableFixedBitfield([
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
        ]));
        fields.put(TcfCaV1Field.PURPOSES_IMPLIED_CONSENT.toString(), new EncodableFixedBitfield([
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
        ]));
        fields.put(TcfCaV1Field.VENDOR_EXPRESS_CONSENT.toString(), new EncodableOptimizedFixedRange([]));
        fields.put(TcfCaV1Field.VENDOR_IMPLIED_CONSENT.toString(), new EncodableOptimizedFixedRange([]));
        fields.put(TcfCaV1Field.PUB_RESTRICTIONS.toString(), new EncodableArrayOfFixedIntegerRanges(6, 2, [], false));
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
            throw new DecodingError("Unable to decode TcfCaV1CoreSegment '" + encodedString + "'");
        }
    }
}
