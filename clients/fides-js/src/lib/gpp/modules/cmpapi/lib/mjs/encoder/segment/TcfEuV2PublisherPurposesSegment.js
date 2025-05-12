import { TraditionalBase64UrlEncoder } from "../base64/TraditionalBase64UrlEncoder.js";
import { BitStringEncoder } from "../bitstring/BitStringEncoder.js";
import { EncodableFixedBitfield } from "../datatype/EncodableFixedBitfield.js";
import { EncodableFixedInteger } from "../datatype/EncodableFixedInteger.js";
import { EncodableFlexibleBitfield } from "../datatype/EncodableFlexibleBitfield.js";
import { DecodingError } from "../error/DecodingError.js";
import { EncodableBitStringFields } from "../field/EncodableBitStringFields.js";
import { TCFEUV2_PUBLISHER_PURPOSES_SEGMENT_FIELD_NAMES } from "../field/TcfEuV2Field.js";
import { TcfEuV2Field } from "../field/TcfEuV2Field.js";
import { AbstractLazilyEncodableSegment } from "./AbstractLazilyEncodableSegment.js";
export class TcfEuV2PublisherPurposesSegment extends AbstractLazilyEncodableSegment {
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
        return TCFEUV2_PUBLISHER_PURPOSES_SEGMENT_FIELD_NAMES;
    }
    // overriden
    initializeFields() {
        let fields = new EncodableBitStringFields();
        fields.put(TcfEuV2Field.PUBLISHER_PURPOSES_SEGMENT_TYPE.toString(), new EncodableFixedInteger(3, 3));
        fields.put(TcfEuV2Field.PUBLISHER_CONSENTS.toString(), new EncodableFixedBitfield([
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
        fields.put(TcfEuV2Field.PUBLISHER_LEGITIMATE_INTERESTS.toString(), new EncodableFixedBitfield([
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
        let numCustomPurposes = new EncodableFixedInteger(6, 0);
        fields.put(TcfEuV2Field.NUM_CUSTOM_PURPOSES.toString(), numCustomPurposes);
        fields.put(TcfEuV2Field.PUBLISHER_CUSTOM_CONSENTS.toString(), new EncodableFlexibleBitfield(() => {
            return numCustomPurposes.getValue();
        }, []));
        fields.put(TcfEuV2Field.PUBLISHER_CUSTOM_LEGITIMATE_INTERESTS.toString(), new EncodableFlexibleBitfield(() => {
            return numCustomPurposes.getValue();
        }, []));
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
            throw new DecodingError("Unable to decode TcfEuV2PublisherPurposesSegment '" + encodedString + "'");
        }
    }
}
