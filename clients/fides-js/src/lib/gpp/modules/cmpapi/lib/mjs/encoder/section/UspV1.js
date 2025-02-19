import { UspV1CoreSegment } from "../segment/UspV1CoreSegment.js";
import { AbstractLazilyEncodableSection } from "./AbstractLazilyEncodableSection.js";
// Deprecated
export class UspV1 extends AbstractLazilyEncodableSection {
    static ID = 6;
    static VERSION = 1;
    static NAME = "uspv1";
    constructor(encodedString) {
        super();
        if (encodedString && encodedString.length > 0) {
            this.decode(encodedString);
        }
    }
    //Overriden
    getId() {
        return UspV1.ID;
    }
    //Overriden
    getName() {
        return UspV1.NAME;
    }
    //Override
    getVersion() {
        return UspV1.VERSION;
    }
    //Overriden
    initializeSegments() {
        let segments = [];
        segments.push(new UspV1CoreSegment());
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
