import { UsUtCoreSegment } from "../segment/UsUtCoreSegment.js";
import { AbstractLazilyEncodableSection } from "./AbstractLazilyEncodableSection.js";
export class UsUt extends AbstractLazilyEncodableSection {
    static ID = 11;
    static VERSION = 1;
    static NAME = "usut";
    constructor(encodedString) {
        super();
        if (encodedString && encodedString.length > 0) {
            this.decode(encodedString);
        }
    }
    //Overriden
    getId() {
        return UsUt.ID;
    }
    //Overriden
    getName() {
        return UsUt.NAME;
    }
    //Override
    getVersion() {
        return UsUt.VERSION;
    }
    //Overriden
    initializeSegments() {
        let segments = [];
        segments.push(new UsUtCoreSegment());
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
