import { UsFlCoreSegment } from "../segment/UsFlCoreSegment.js";
import { AbstractLazilyEncodableSection } from "./AbstractLazilyEncodableSection.js";
export class UsFl extends AbstractLazilyEncodableSection {
    static ID = 13;
    static VERSION = 1;
    static NAME = "usfl";
    constructor(encodedString) {
        super();
        if (encodedString && encodedString.length > 0) {
            this.decode(encodedString);
        }
    }
    //Overriden
    getId() {
        return UsFl.ID;
    }
    //Overriden
    getName() {
        return UsFl.NAME;
    }
    //Override
    getVersion() {
        return UsFl.VERSION;
    }
    //Overriden
    initializeSegments() {
        let segments = [];
        segments.push(new UsFlCoreSegment());
        return segments;
    }
    //Overriden
    decodeSection(encodedString) {
        let segments = this.initializeSegments();
        if (encodedString != null && encodedString.length !== 0) {
            let encodedSegments = encodedString.split(".");
            for (let i = 0; i < segments.length; i++) {
                if (encodedSegments.length > i) {
                    segments[i].decode(encodedSegments[i]);
                }
            }
        }
        return segments;
    }
    // Overriden
    encodeSection(segments) {
        let encodedSegments = [];
        for (let i = 0; i < segments.length; i++) {
            let segment = segments[i];
            encodedSegments.push(segment.encode());
        }
        return encodedSegments.join(".");
    }
}
