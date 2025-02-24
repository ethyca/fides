import { AbstractLazilyEncodableSection } from "./AbstractLazilyEncodableSection.js";
import { HeaderV1CoreSegment } from "../segment/HeaderV1CoreSegment.js";
export class HeaderV1 extends AbstractLazilyEncodableSection {
    static ID = 3;
    static VERSION = 1;
    static NAME = "header";
    constructor(encodedString) {
        super();
        if (encodedString && encodedString.length > 0) {
            this.decode(encodedString);
        }
    }
    //Overriden
    getId() {
        return HeaderV1.ID;
    }
    //Overriden
    getName() {
        return HeaderV1.NAME;
    }
    //Override
    getVersion() {
        return HeaderV1.VERSION;
    }
    //Overriden
    initializeSegments() {
        let segments = [];
        segments.push(new HeaderV1CoreSegment());
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
