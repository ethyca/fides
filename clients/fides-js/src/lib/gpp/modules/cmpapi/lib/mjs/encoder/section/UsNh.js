import { UsNhField } from "../field/UsNhField.js";
import { UsNhCoreSegment } from "../segment/UsNhCoreSegment.js";
import { UsNhGpcSegment } from "../segment/UsNhGpcSegment.js";
import { AbstractLazilyEncodableSection } from "./AbstractLazilyEncodableSection.js";
export class UsNh extends AbstractLazilyEncodableSection {
    static ID = 20;
    static VERSION = 1;
    static NAME = "usnh";
    constructor(encodedString) {
        super();
        if (encodedString && encodedString.length > 0) {
            this.decode(encodedString);
        }
    }
    //Overriden
    getId() {
        return UsNh.ID;
    }
    //Overriden
    getName() {
        return UsNh.NAME;
    }
    //Override
    getVersion() {
        return UsNh.VERSION;
    }
    //Overriden
    initializeSegments() {
        let segments = [];
        segments.push(new UsNhCoreSegment());
        segments.push(new UsNhGpcSegment());
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
                segments[1].setFieldValue(UsNhField.GPC_SEGMENT_INCLUDED, true);
                segments[1].decode(encodedSegments[1]);
            }
            else {
                segments[1].setFieldValue(UsNhField.GPC_SEGMENT_INCLUDED, false);
            }
        }
        return segments;
    }
    // Overriden
    encodeSection(segments) {
        let encodedSegments = [];
        if (segments.length >= 1) {
            encodedSegments.push(segments[0].encode());
            if (segments.length >= 2 && segments[1].getFieldValue(UsNhField.GPC_SEGMENT_INCLUDED) === true) {
                encodedSegments.push(segments[1].encode());
            }
        }
        return encodedSegments.join(".");
    }
}
