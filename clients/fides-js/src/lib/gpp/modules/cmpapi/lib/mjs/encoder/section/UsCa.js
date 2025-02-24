import { UsCaField } from "../field/UsCaField.js";
import { UsCaCoreSegment } from "../segment/UsCaCoreSegment.js";
import { UsCaGpcSegment } from "../segment/UsCaGpcSegment.js";
import { AbstractLazilyEncodableSection } from "./AbstractLazilyEncodableSection.js";
export class UsCa extends AbstractLazilyEncodableSection {
    static ID = 8;
    static VERSION = 1;
    static NAME = "usca";
    constructor(encodedString) {
        super();
        if (encodedString && encodedString.length > 0) {
            this.decode(encodedString);
        }
    }
    //Overriden
    getId() {
        return UsCa.ID;
    }
    //Overriden
    getName() {
        return UsCa.NAME;
    }
    //Override
    getVersion() {
        return UsCa.VERSION;
    }
    //Overriden
    initializeSegments() {
        let segments = [];
        segments.push(new UsCaCoreSegment());
        segments.push(new UsCaGpcSegment());
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
                segments[1].setFieldValue(UsCaField.GPC_SEGMENT_INCLUDED, true);
                segments[1].decode(encodedSegments[1]);
            }
            else {
                segments[1].setFieldValue(UsCaField.GPC_SEGMENT_INCLUDED, false);
            }
        }
        return segments;
    }
    // Overriden
    encodeSection(segments) {
        let encodedSegments = [];
        if (segments.length >= 1) {
            encodedSegments.push(segments[0].encode());
            if (segments.length >= 2 && segments[1].getFieldValue(UsCaField.GPC_SEGMENT_INCLUDED) === true) {
                encodedSegments.push(segments[1].encode());
            }
        }
        return encodedSegments.join(".");
    }
}
