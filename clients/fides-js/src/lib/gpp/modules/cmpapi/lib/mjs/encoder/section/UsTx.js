import { UsTxField } from "../field/UsTxField.js";
import { UsTxCoreSegment } from "../segment/UsTxCoreSegment.js";
import { UsTxGpcSegment } from "../segment/UsTxGpcSegment.js";
import { AbstractLazilyEncodableSection } from "./AbstractLazilyEncodableSection.js";
export class UsTx extends AbstractLazilyEncodableSection {
    static ID = 16;
    static VERSION = 1;
    static NAME = "ustx";
    constructor(encodedString) {
        super();
        if (encodedString && encodedString.length > 0) {
            this.decode(encodedString);
        }
    }
    //Overriden
    getId() {
        return UsTx.ID;
    }
    //Overriden
    getName() {
        return UsTx.NAME;
    }
    //Override
    getVersion() {
        return UsTx.VERSION;
    }
    //Overriden
    initializeSegments() {
        let segments = [];
        segments.push(new UsTxCoreSegment());
        segments.push(new UsTxGpcSegment());
        return segments;
    }
    //Overriden
    decodeSection(encodedString) {
        let segments = this.initializeSegments();
        if (encodedString != null && encodedString.length !== 0) {
            let encodedSegments = encodedString.split(".");
            if (encodedSegments.length > 0) {
                segments[0].decode(encodedSegments[0]);
            }
            if (encodedSegments.length > 1) {
                segments[1].setFieldValue(UsTxField.GPC_SEGMENT_INCLUDED, true);
                segments[1].decode(encodedSegments[1]);
            }
            else {
                segments[1].setFieldValue(UsTxField.GPC_SEGMENT_INCLUDED, false);
            }
        }
        return segments;
    }
    // Overriden
    encodeSection(segments) {
        let encodedSegments = [];
        if (segments.length >= 1) {
            encodedSegments.push(segments[0].encode());
            if (segments.length >= 2 && segments[1].getFieldValue(UsTxField.GPC_SEGMENT_INCLUDED) === true) {
                encodedSegments.push(segments[1].encode());
            }
        }
        return encodedSegments.join(".");
    }
}
