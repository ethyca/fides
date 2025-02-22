import { DecodingError } from "../error/DecodingError.js";
import { TcfEuV2Field } from "../field/TcfEuV2Field.js";
import { TcfEuV2CoreSegment } from "../segment/TcfEuV2CoreSegment.js";
import { TcfEuV2PublisherPurposesSegment } from "../segment/TcfEuV2PublisherPurposesSegment.js";
import { TcfEuV2VendorsAllowedSegment } from "../segment/TcfEuV2VendorsAllowedSegment.js";
import { TcfEuV2VendorsDisclosedSegment } from "../segment/TcfEuV2VendorsDisclosedSegment.js";
import { AbstractLazilyEncodableSection } from "./AbstractLazilyEncodableSection.js";
export class TcfEuV2 extends AbstractLazilyEncodableSection {
    static ID = 2;
    static VERSION = 2;
    static NAME = "tcfeuv2";
    constructor(encodedString) {
        super();
        if (encodedString && encodedString.length > 0) {
            this.decode(encodedString);
        }
    }
    //Overriden
    getId() {
        return TcfEuV2.ID;
    }
    //Overriden
    getName() {
        return TcfEuV2.NAME;
    }
    //Override
    getVersion() {
        return TcfEuV2.VERSION;
    }
    //Overriden
    initializeSegments() {
        let segments = [];
        segments.push(new TcfEuV2CoreSegment());
        segments.push(new TcfEuV2PublisherPurposesSegment());
        segments.push(new TcfEuV2VendorsAllowedSegment());
        segments.push(new TcfEuV2VendorsDisclosedSegment());
        return segments;
    }
    //Overriden
    decodeSection(encodedString) {
        let segments = this.initializeSegments();
        if (encodedString != null && encodedString.length !== 0) {
            let encodedSegments = encodedString.split(".");
            for (let i = 0; i < encodedSegments.length; i++) {
                /**
                 * The first 3 bits contain the segment id. Rather than decode the entire string, just check the first character.
                 *
                 * A-H     = '000' = 0
                 * I-P     = '001' = 1
                 * Q-X     = '010' = 2
                 * Y-Z,a-f = '011' = 3
                 *
                 * Note that there is no segment id field for the core segment. Instead the first 6 bits are reserved
                 * for the encoding version which only coincidentally works here because the version value is less than 8.
                 */
                let encodedSegment = encodedSegments[i];
                if (encodedSegment.length !== 0) {
                    let firstChar = encodedSegment.charAt(0);
                    // unfortunately, the segment ordering doesn't match the segment ids
                    if (firstChar >= "A" && firstChar <= "H") {
                        segments[0].decode(encodedSegments[i]);
                    }
                    else if (firstChar >= "I" && firstChar <= "P") {
                        segments[3].decode(encodedSegments[i]);
                    }
                    else if (firstChar >= "Q" && firstChar <= "X") {
                        segments[2].decode(encodedSegments[i]);
                    }
                    else if ((firstChar >= "Y" && firstChar <= "Z") || (firstChar >= "a" && firstChar <= "f")) {
                        segments[1].decode(encodedSegments[i]);
                    }
                    else {
                        throw new DecodingError("Unable to decode TcfEuV2 segment '" + encodedSegment + "'");
                    }
                }
            }
        }
        return segments;
    }
    // Overriden
    encodeSection(segments) {
        let encodedSegments = [];
        if (segments.length >= 1) {
            encodedSegments.push(segments[0].encode());
            let isServiceSpecific = this.getFieldValue(TcfEuV2Field.IS_SERVICE_SPECIFIC);
            if (isServiceSpecific) {
                if (segments.length >= 2) {
                    encodedSegments.push(segments[1].encode());
                }
            }
            else {
                if (segments.length >= 2) {
                    encodedSegments.push(segments[2].encode());
                    if (segments.length >= 3) {
                        encodedSegments.push(segments[3].encode());
                    }
                }
            }
        }
        return encodedSegments.join(".");
    }
    //Overriden
    setFieldValue(fieldName, value) {
        super.setFieldValue(fieldName, value);
        if (fieldName !== TcfEuV2Field.CREATED && fieldName !== TcfEuV2Field.LAST_UPDATED) {
            let date = new Date();
            super.setFieldValue(TcfEuV2Field.CREATED, date);
            super.setFieldValue(TcfEuV2Field.LAST_UPDATED, date);
        }
    }
}
