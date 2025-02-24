import { UsDeField } from "../field/UsDeField.js";
import { UsDeCoreSegment } from "../segment/UsDeCoreSegment.js";
import { UsDeGpcSegment } from "../segment/UsDeGpcSegment.js";
import { AbstractLazilyEncodableSection } from "./AbstractLazilyEncodableSection.js";
export class UsDe extends AbstractLazilyEncodableSection {
    static ID = 17;
    static VERSION = 1;
    static NAME = "usde";
    constructor(encodedString) {
        super();
        if (encodedString && encodedString.length > 0) {
            this.decode(encodedString);
        }
    }
    //Overriden
    getId() {
        return UsDe.ID;
    }
    //Overriden
    getName() {
        return UsDe.NAME;
    }
    //Override
    getVersion() {
        return UsDe.VERSION;
    }
    //Overriden
    initializeSegments() {
        let segments = [];
        segments.push(new UsDeCoreSegment());
        segments.push(new UsDeGpcSegment());
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
                segments[1].setFieldValue(UsDeField.GPC_SEGMENT_INCLUDED, true);
                segments[1].decode(encodedSegments[1]);
            }
            else {
                segments[1].setFieldValue(UsDeField.GPC_SEGMENT_INCLUDED, false);
            }
        }
        return segments;
    }
    // Overriden
    encodeSection(segments) {
        let encodedSegments = [];
        if (segments.length >= 1) {
            encodedSegments.push(segments[0].encode());
            if (segments.length >= 2 && segments[1].getFieldValue(UsDeField.GPC_SEGMENT_INCLUDED) === true) {
                encodedSegments.push(segments[1].encode());
            }
        }
        return encodedSegments.join(".");
    }
}
