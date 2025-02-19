import { UsCtField } from "../field/UsCtField.js";
import { UsCtCoreSegment } from "../segment/UsCtCoreSegment.js";
import { UsCtGpcSegment } from "../segment/UsCtGpcSegment.js";
import { AbstractLazilyEncodableSection } from "./AbstractLazilyEncodableSection.js";
export class UsCt extends AbstractLazilyEncodableSection {
    static ID = 12;
    static VERSION = 1;
    static NAME = "usct";
    constructor(encodedString) {
        super();
        if (encodedString && encodedString.length > 0) {
            this.decode(encodedString);
        }
    }
    //Overriden
    getId() {
        return UsCt.ID;
    }
    //Overriden
    getName() {
        return UsCt.NAME;
    }
    //Override
    getVersion() {
        return UsCt.VERSION;
    }
    //Overriden
    initializeSegments() {
        let segments = [];
        segments.push(new UsCtCoreSegment());
        segments.push(new UsCtGpcSegment());
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
                segments[1].setFieldValue(UsCtField.GPC_SEGMENT_INCLUDED, true);
                segments[1].decode(encodedSegments[1]);
            }
            else {
                segments[1].setFieldValue(UsCtField.GPC_SEGMENT_INCLUDED, false);
            }
        }
        return segments;
    }
    // Overriden
    encodeSection(segments) {
        let encodedSegments = [];
        if (segments.length >= 1) {
            encodedSegments.push(segments[0].encode());
            if (segments.length >= 2 && segments[1].getFieldValue(UsCtField.GPC_SEGMENT_INCLUDED) === true) {
                encodedSegments.push(segments[1].encode());
            }
        }
        return encodedSegments.join(".");
    }
}
