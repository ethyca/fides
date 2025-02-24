import { UsIaField } from "../field/UsIaField.js";
import { UsIaCoreSegment } from "../segment/UsIaCoreSegment.js";
import { UsIaGpcSegment } from "../segment/UsIaGpcSegment.js";
import { AbstractLazilyEncodableSection } from "./AbstractLazilyEncodableSection.js";
export class UsIa extends AbstractLazilyEncodableSection {
    static ID = 18;
    static VERSION = 1;
    static NAME = "usia";
    constructor(encodedString) {
        super();
        if (encodedString && encodedString.length > 0) {
            this.decode(encodedString);
        }
    }
    //Overriden
    getId() {
        return UsIa.ID;
    }
    //Overriden
    getName() {
        return UsIa.NAME;
    }
    //Override
    getVersion() {
        return UsIa.VERSION;
    }
    //Overriden
    initializeSegments() {
        let segments = [];
        segments.push(new UsIaCoreSegment());
        segments.push(new UsIaGpcSegment());
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
                segments[1].setFieldValue(UsIaField.GPC_SEGMENT_INCLUDED, true);
                segments[1].decode(encodedSegments[1]);
            }
            else {
                segments[1].setFieldValue(UsIaField.GPC_SEGMENT_INCLUDED, false);
            }
        }
        return segments;
    }
    // Overriden
    encodeSection(segments) {
        let encodedSegments = [];
        if (segments.length >= 1) {
            encodedSegments.push(segments[0].encode());
            if (segments.length >= 2 && segments[1].getFieldValue(UsIaField.GPC_SEGMENT_INCLUDED) === true) {
                encodedSegments.push(segments[1].encode());
            }
        }
        return encodedSegments.join(".");
    }
}
