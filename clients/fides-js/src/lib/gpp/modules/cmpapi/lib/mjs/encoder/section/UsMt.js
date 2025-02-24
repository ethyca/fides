import { UsMtField } from "../field/UsMtField.js";
import { UsMtCoreSegment } from "../segment/UsMtCoreSegment.js";
import { UsMtGpcSegment } from "../segment/UsMtGpcSegment.js";
import { AbstractLazilyEncodableSection } from "./AbstractLazilyEncodableSection.js";
export class UsMt extends AbstractLazilyEncodableSection {
    static ID = 14;
    static VERSION = 1;
    static NAME = "usmt";
    constructor(encodedString) {
        super();
        if (encodedString && encodedString.length > 0) {
            this.decode(encodedString);
        }
    }
    //Overriden
    getId() {
        return UsMt.ID;
    }
    //Overriden
    getName() {
        return UsMt.NAME;
    }
    //Override
    getVersion() {
        return UsMt.VERSION;
    }
    //Overriden
    initializeSegments() {
        let segments = [];
        segments.push(new UsMtCoreSegment());
        segments.push(new UsMtGpcSegment());
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
                segments[1].setFieldValue(UsMtField.GPC_SEGMENT_INCLUDED, true);
                segments[1].decode(encodedSegments[1]);
            }
            else {
                segments[1].setFieldValue(UsMtField.GPC_SEGMENT_INCLUDED, false);
            }
        }
        return segments;
    }
    // Overriden
    encodeSection(segments) {
        let encodedSegments = [];
        if (segments.length >= 1) {
            encodedSegments.push(segments[0].encode());
            if (segments.length >= 2 && segments[1].getFieldValue(UsMtField.GPC_SEGMENT_INCLUDED) === true) {
                encodedSegments.push(segments[1].encode());
            }
        }
        return encodedSegments.join(".");
    }
}
