import { AbstractLazilyEncodableSection } from "./AbstractLazilyEncodableSection.js";
import { UsNatField } from "../field/UsNatField.js";
import { UsNatCoreSegment } from "../segment/UsNatCoreSegment.js";
import { UsNatGpcSegment } from "../segment/UsNatGpcSegment.js";
export class UsNat extends AbstractLazilyEncodableSection {
    static ID = 7;
    static VERSION = 1;
    static NAME = "usnat";
    constructor(encodedString) {
        super();
        if (encodedString && encodedString.length > 0) {
            this.decode(encodedString);
        }
    }
    //Overriden
    getId() {
        return UsNat.ID;
    }
    //Overriden
    getName() {
        return UsNat.NAME;
    }
    //Override
    getVersion() {
        return UsNat.VERSION;
    }
    //Overriden
    initializeSegments() {
        let segments = [];
        segments.push(new UsNatCoreSegment());
        segments.push(new UsNatGpcSegment());
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
                segments[1].setFieldValue(UsNatField.GPC_SEGMENT_INCLUDED, true);
                segments[1].decode(encodedSegments[1]);
            }
            else {
                segments[1].setFieldValue(UsNatField.GPC_SEGMENT_INCLUDED, false);
            }
        }
        return segments;
    }
    // Overriden
    encodeSection(segments) {
        let encodedSegments = [];
        if (segments.length >= 1) {
            encodedSegments.push(segments[0].encode());
            if (segments.length >= 2 && segments[1].getFieldValue(UsNatField.GPC_SEGMENT_INCLUDED) === true) {
                encodedSegments.push(segments[1].encode());
            }
        }
        return encodedSegments.join(".");
    }
}
