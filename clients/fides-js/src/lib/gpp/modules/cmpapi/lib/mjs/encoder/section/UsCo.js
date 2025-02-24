import { AbstractLazilyEncodableSection } from "./AbstractLazilyEncodableSection.js";
import { UsCoField } from "../field/UsCoField.js";
import { UsCoCoreSegment } from "../segment/UsCoCoreSegment.js";
import { UsCoGpcSegment } from "../segment/UsCoGpcSegment.js";
export class UsCo extends AbstractLazilyEncodableSection {
    static ID = 10;
    static VERSION = 1;
    static NAME = "usco";
    constructor(encodedString) {
        super();
        if (encodedString && encodedString.length > 0) {
            this.decode(encodedString);
        }
    }
    //Overriden
    getId() {
        return UsCo.ID;
    }
    //Overriden
    getName() {
        return UsCo.NAME;
    }
    //Override
    getVersion() {
        return UsCo.VERSION;
    }
    //Overriden
    initializeSegments() {
        let segments = [];
        segments.push(new UsCoCoreSegment());
        segments.push(new UsCoGpcSegment());
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
                segments[1].setFieldValue(UsCoField.GPC_SEGMENT_INCLUDED, true);
                segments[1].decode(encodedSegments[1]);
            }
            else {
                segments[1].setFieldValue(UsCoField.GPC_SEGMENT_INCLUDED, false);
            }
        }
        return segments;
    }
    // Overriden
    encodeSection(segments) {
        let encodedSegments = [];
        if (segments.length >= 1) {
            encodedSegments.push(segments[0].encode());
            if (segments.length >= 2 && segments[1].getFieldValue(UsCoField.GPC_SEGMENT_INCLUDED) === true) {
                encodedSegments.push(segments[1].encode());
            }
        }
        return encodedSegments.join(".");
    }
}
