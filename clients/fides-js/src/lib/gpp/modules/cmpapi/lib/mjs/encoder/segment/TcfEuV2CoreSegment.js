import { TraditionalBase64UrlEncoder } from "../base64/TraditionalBase64UrlEncoder.js";
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
import { TCFEUV2_CORE_SEGMENT_FIELD_NAMES } from "../field/TcfEuV2Field.js";
import { TcfEuV2Field } from "../field/TcfEuV2Field.js";
import { TcfEuV2 } from "../section/TcfEuV2.js";
import { AbstractLazilyEncodableSegment } from "./AbstractLazilyEncodableSegment.js";
export class TcfEuV2CoreSegment extends AbstractLazilyEncodableSegment {
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
        return TCFEUV2_CORE_SEGMENT_FIELD_NAMES;
    }
    // overriden
    initializeFields() {
        let date = new Date();
        let fields = new EncodableBitStringFields();
        fields.put(TcfEuV2Field.VERSION.toString(), new EncodableFixedInteger(6, TcfEuV2.VERSION));
        fields.put(TcfEuV2Field.CREATED.toString(), new EncodableDatetime(date));
        fields.put(TcfEuV2Field.LAST_UPDATED.toString(), new EncodableDatetime(date));
        fields.put(TcfEuV2Field.CMP_ID.toString(), new EncodableFixedInteger(12, 0));
        fields.put(TcfEuV2Field.CMP_VERSION.toString(), new EncodableFixedInteger(12, 0));
        fields.put(TcfEuV2Field.CONSENT_SCREEN.toString(), new EncodableFixedInteger(6, 0));
        fields.put(TcfEuV2Field.CONSENT_LANGUAGE.toString(), new EncodableFixedString(2, "EN"));
        fields.put(TcfEuV2Field.VENDOR_LIST_VERSION.toString(), new EncodableFixedInteger(12, 0));
        fields.put(TcfEuV2Field.POLICY_VERSION.toString(), new EncodableFixedInteger(6, 2));
        fields.put(TcfEuV2Field.IS_SERVICE_SPECIFIC.toString(), new EncodableBoolean(false));
        fields.put(TcfEuV2Field.USE_NON_STANDARD_STACKS.toString(), new EncodableBoolean(false));
        fields.put(TcfEuV2Field.SPECIAL_FEATURE_OPTINS.toString(), new EncodableFixedBitfield([false, false, false, false, false, false, false, false, false, false, false, false]));
        fields.put(TcfEuV2Field.PURPOSE_CONSENTS.toString(), new EncodableFixedBitfield([
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
        fields.put(TcfEuV2Field.PURPOSE_LEGITIMATE_INTERESTS.toString(), new EncodableFixedBitfield([
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
        fields.put(TcfEuV2Field.PURPOSE_ONE_TREATMENT.toString(), new EncodableBoolean(false));
        fields.put(TcfEuV2Field.PUBLISHER_COUNTRY_CODE.toString(), new EncodableFixedString(2, "AA"));
        fields.put(TcfEuV2Field.VENDOR_CONSENTS.toString(), new EncodableOptimizedFixedRange([]));
        fields.put(TcfEuV2Field.VENDOR_LEGITIMATE_INTERESTS.toString(), new EncodableOptimizedFixedRange([]));
        fields.put(TcfEuV2Field.PUBLISHER_RESTRICTIONS.toString(), new EncodableArrayOfFixedIntegerRanges(6, 2, [], false));
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
            throw new DecodingError("Unable to decode TcfEuV2CoreSegment '" + encodedString + "'");
        }
    }
}
