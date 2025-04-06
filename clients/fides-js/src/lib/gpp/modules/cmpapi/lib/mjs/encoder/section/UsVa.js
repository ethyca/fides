import { UsVaCoreSegment } from "../segment/UsVaCoreSegment.js";
import { AbstractLazilyEncodableSection } from "./AbstractLazilyEncodableSection.js";
export class UsVa extends AbstractLazilyEncodableSection {
    static ID = 9;
    static VERSION = 1;
    static NAME = "usva";
    constructor(encodedString) {
        super();
        if (encodedString && encodedString.length > 0) {
            this.decode(encodedString);
        }
    }
    //Overriden
    getId() {
        return UsVa.ID;
    }
    //Overriden
    getName() {
        return UsVa.NAME;
    }
    //Override
    getVersion() {
        return UsVa.VERSION;
    }
    //Overriden
    initializeSegments() {
        let segments = [];
        segments.push(new UsVaCoreSegment());
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
