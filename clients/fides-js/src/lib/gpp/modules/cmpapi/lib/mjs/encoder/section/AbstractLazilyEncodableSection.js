import { InvalidFieldError } from "../error/InvalidFieldError.js";
export class AbstractLazilyEncodableSection {
    segments;
    encodedString = null;
    dirty = false;
    decoded = true;
    constructor() {
        this.segments = this.initializeSegments();
    }
    hasField(fieldName) {
        if (!this.decoded) {
            this.segments = this.decodeSection(this.encodedString);
            this.dirty = false;
            this.decoded = true;
        }
        for (let i = 0; i < this.segments.length; i++) {
            let segment = this.segments[i];
            if (segment.getFieldNames().includes(fieldName)) {
                return segment.hasField(fieldName);
            }
        }
        return false;
    }
    getFieldValue(fieldName) {
        if (!this.decoded) {
            this.segments = this.decodeSection(this.encodedString);
            this.dirty = false;
            this.decoded = true;
        }
        for (let i = 0; i < this.segments.length; i++) {
            let segment = this.segments[i];
            if (segment.hasField(fieldName)) {
                return segment.getFieldValue(fieldName);
            }
        }
        throw new InvalidFieldError("Invalid field: '" + fieldName + "'");
    }
    setFieldValue(fieldName, value) {
        if (!this.decoded) {
            this.segments = this.decodeSection(this.encodedString);
            this.dirty = false;
            this.decoded = true;
        }
        for (let i = 0; i < this.segments.length; i++) {
            let segment = this.segments[i];
            if (segment.hasField(fieldName)) {
                segment.setFieldValue(fieldName, value);
                return;
            }
        }
        throw new InvalidFieldError("Invalid field: '" + fieldName + "'");
    }
    //Overriden
    toObj() {
        let obj = {};
        for (let i = 0; i < this.segments.length; i++) {
            let segmentObject = this.segments[i].toObj();
            for (const [fieldName, value] of Object.entries(segmentObject)) {
                obj[fieldName] = value;
            }
        }
        return obj;
    }
    encode() {
        if (this.encodedString == null || this.encodedString.length === 0 || this.dirty) {
            this.encodedString = this.encodeSection(this.segments);
            this.dirty = false;
            this.decoded = true;
        }
        return this.encodedString;
    }
    decode(encodedString) {
        this.encodedString = encodedString;
        this.segments = this.decodeSection(this.encodedString);
        this.dirty = false;
        this.decoded = false;
    }
    setIsDirty(status) {
        this.dirty = status;
    }
}
