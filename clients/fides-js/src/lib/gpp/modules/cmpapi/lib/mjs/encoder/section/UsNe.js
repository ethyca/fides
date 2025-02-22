import { UsNeField } from "../field/UsNeField.js";
import { UsNeCoreSegment } from "../segment/UsNeCoreSegment.js";
import { UsNeGpcSegment } from "../segment/UsNeGpcSegment.js";
import { AbstractLazilyEncodableSection } from "./AbstractLazilyEncodableSection.js";
export class UsNe extends AbstractLazilyEncodableSection {
    static ID = 19;
    static VERSION = 1;
    static NAME = "usne";
    constructor(encodedString) {
        super();
        if (encodedString && encodedString.length > 0) {
            this.decode(encodedString);
        }
    }
    //Overriden
    getId() {
        return UsNe.ID;
    }
    //Overriden
    getName() {
        return UsNe.NAME;
    }
    //Override
    getVersion() {
        return UsNe.VERSION;
    }
    //Overriden
    initializeSegments() {
        let segments = [];
        segments.push(new UsNeCoreSegment());
        segments.push(new UsNeGpcSegment());
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
                segments[1].setFieldValue(UsNeField.GPC_SEGMENT_INCLUDED, true);
                segments[1].decode(encodedSegments[1]);
            }
            else {
                segments[1].setFieldValue(UsNeField.GPC_SEGMENT_INCLUDED, false);
            }
        }
        return segments;
    }
    // Overriden
    encodeSection(segments) {
        let encodedSegments = [];
        if (segments.length >= 1) {
            encodedSegments.push(segments[0].encode());
            if (segments.length >= 2 && segments[1].getFieldValue(UsNeField.GPC_SEGMENT_INCLUDED) === true) {
                encodedSegments.push(segments[1].encode());
            }
        }
        return encodedSegments.join(".");
    }
}
