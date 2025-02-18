import { UsTnField } from "../field/UsTnField.js";
import { UsTnCoreSegment } from "../segment/UsTnCoreSegment.js";
import { UsTnGpcSegment } from "../segment/UsTnGpcSegment.js";
import { AbstractLazilyEncodableSection } from "./AbstractLazilyEncodableSection.js";
export class UsTn extends AbstractLazilyEncodableSection {
    static ID = 22;
    static VERSION = 1;
    static NAME = "ustn";
    constructor(encodedString) {
        super();
        if (encodedString && encodedString.length > 0) {
            this.decode(encodedString);
        }
    }
    //Overriden
    getId() {
        return UsTn.ID;
    }
    //Overriden
    getName() {
        return UsTn.NAME;
    }
    //Override
    getVersion() {
        return UsTn.VERSION;
    }
    //Overriden
    initializeSegments() {
        let segments = [];
        segments.push(new UsTnCoreSegment());
        segments.push(new UsTnGpcSegment());
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
                segments[1].setFieldValue(UsTnField.GPC_SEGMENT_INCLUDED, true);
                segments[1].decode(encodedSegments[1]);
            }
            else {
                segments[1].setFieldValue(UsTnField.GPC_SEGMENT_INCLUDED, false);
            }
        }
        return segments;
    }
    // Overriden
    encodeSection(segments) {
        let encodedSegments = [];
        if (segments.length >= 1) {
            encodedSegments.push(segments[0].encode());
            if (segments.length >= 2 && segments[1].getFieldValue(UsTnField.GPC_SEGMENT_INCLUDED) === true) {
                encodedSegments.push(segments[1].encode());
            }
        }
        return encodedSegments.join(".");
    }
}
