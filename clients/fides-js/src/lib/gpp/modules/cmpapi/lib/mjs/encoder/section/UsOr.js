import { UsOrField } from "../field/UsOrField.js";
import { UsOrCoreSegment } from "../segment/UsOrCoreSegment.js";
import { UsOrGpcSegment } from "../segment/UsOrGpcSegment.js";
import { AbstractLazilyEncodableSection } from "./AbstractLazilyEncodableSection.js";
export class UsOr extends AbstractLazilyEncodableSection {
    static ID = 15;
    static VERSION = 1;
    static NAME = "usor";
    constructor(encodedString) {
        super();
        if (encodedString && encodedString.length > 0) {
            this.decode(encodedString);
        }
    }
    //Overriden
    getId() {
        return UsOr.ID;
    }
    //Overriden
    getName() {
        return UsOr.NAME;
    }
    //Override
    getVersion() {
        return UsOr.VERSION;
    }
    //Overriden
    initializeSegments() {
        let segments = [];
        segments.push(new UsOrCoreSegment());
        segments.push(new UsOrGpcSegment());
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
                segments[1].setFieldValue(UsOrField.GPC_SEGMENT_INCLUDED, true);
                segments[1].decode(encodedSegments[1]);
            }
            else {
                segments[1].setFieldValue(UsOrField.GPC_SEGMENT_INCLUDED, false);
            }
        }
        return segments;
    }
    // Overriden
    encodeSection(segments) {
        let encodedSegments = [];
        if (segments.length >= 1) {
            encodedSegments.push(segments[0].encode());
            if (segments.length >= 2 && segments[1].getFieldValue(UsOrField.GPC_SEGMENT_INCLUDED) === true) {
                encodedSegments.push(segments[1].encode());
            }
        }
        return encodedSegments.join(".");
    }
}
