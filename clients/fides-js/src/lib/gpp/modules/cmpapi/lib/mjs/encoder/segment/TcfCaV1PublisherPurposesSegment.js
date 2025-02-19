import { CompressedBase64UrlEncoder } from "../base64/CompressedBase64UrlEncoder.js";
import { BitStringEncoder } from "../bitstring/BitStringEncoder.js";
import { EncodableFixedBitfield } from "../datatype/EncodableFixedBitfield.js";
import { EncodableFixedInteger } from "../datatype/EncodableFixedInteger.js";
import { EncodableFlexibleBitfield } from "../datatype/EncodableFlexibleBitfield.js";
import { DecodingError } from "../error/DecodingError.js";
import { EncodableBitStringFields } from "../field/EncodableBitStringFields.js";
import { TCFCAV1_PUBLISHER_PURPOSES_SEGMENT_FIELD_NAMES } from "../field/TcfCaV1Field.js";
import { TcfCaV1Field } from "../field/TcfCaV1Field.js";
import { AbstractLazilyEncodableSegment } from "./AbstractLazilyEncodableSegment.js";
export class TcfCaV1PublisherPurposesSegment extends AbstractLazilyEncodableSegment {
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
        return TCFCAV1_PUBLISHER_PURPOSES_SEGMENT_FIELD_NAMES;
    }
    // overriden
    initializeFields() {
        let fields = new EncodableBitStringFields();
        fields.put(TcfCaV1Field.PUB_PURPOSES_SEGMENT_TYPE.toString(), new EncodableFixedInteger(3, 3));
        fields.put(TcfCaV1Field.PUB_PURPOSES_EXPRESS_CONSENT.toString(), new EncodableFixedBitfield([
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
        fields.put(TcfCaV1Field.PUB_PURPOSES_IMPLIED_CONSENT.toString(), new EncodableFixedBitfield([
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
        fields.put(TcfCaV1Field.NUM_CUSTOM_PURPOSES.toString(), numCustomPurposes);
        fields.put(TcfCaV1Field.CUSTOM_PURPOSES_EXPRESS_CONSENT.toString(), new EncodableFlexibleBitfield(() => {
            return numCustomPurposes.getValue();
        }, []));
        fields.put(TcfCaV1Field.CUSTOM_PURPOSES_IMPLIED_CONSENT.toString(), new EncodableFlexibleBitfield(() => {
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
            throw new DecodingError("Unable to decode TcfCaV1PublisherPurposesSegment '" + encodedString + "'");
        }
    }
}
