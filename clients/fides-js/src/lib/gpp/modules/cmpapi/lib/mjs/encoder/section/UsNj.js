import { UsNjField } from "../field/UsNjField.js";
import { UsNjCoreSegment } from "../segment/UsNjCoreSegment.js";
import { UsNjGpcSegment } from "../segment/UsNjGpcSegment.js";
import { AbstractLazilyEncodableSection } from "./AbstractLazilyEncodableSection.js";
export class UsNj extends AbstractLazilyEncodableSection {
    static ID = 21;
    static VERSION = 1;
    static NAME = "usnj";
    constructor(encodedString) {
        super();
        if (encodedString && encodedString.length > 0) {
            this.decode(encodedString);
        }
    }
    //Overriden
    getId() {
        return UsNj.ID;
    }
    //Overriden
    getName() {
        return UsNj.NAME;
    }
    //Override
    getVersion() {
        return UsNj.VERSION;
    }
    //Overriden
    initializeSegments() {
        let segments = [];
        segments.push(new UsNjCoreSegment());
        segments.push(new UsNjGpcSegment());
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
                segments[1].setFieldValue(UsNjField.GPC_SEGMENT_INCLUDED, true);
                segments[1].decode(encodedSegments[1]);
            }
            else {
                segments[1].setFieldValue(UsNjField.GPC_SEGMENT_INCLUDED, false);
            }
        }
        return segments;
    }
    // Overriden
    encodeSection(segments) {
        let encodedSegments = [];
        if (segments.length >= 1) {
            encodedSegments.push(segments[0].encode());
            if (segments.length >= 2 && segments[1].getFieldValue(UsNjField.GPC_SEGMENT_INCLUDED) === true) {
                encodedSegments.push(segments[1].encode());
            }
        }
        return encodedSegments.join(".");
    }
}
