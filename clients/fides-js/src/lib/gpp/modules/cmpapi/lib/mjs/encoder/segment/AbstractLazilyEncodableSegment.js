import { InvalidFieldError } from "../error/InvalidFieldError.js";
export class AbstractLazilyEncodableSegment {
    fields;
    encodedString = null;
    dirty = false;
    decoded = true;
    constructor() {
        this.fields = this.initializeFields();
    }
    //Overriden
    validate() { }
    hasField(fieldName) {
        return this.fields.containsKey(fieldName);
    }
    getFieldValue(fieldName) {
        if (!this.decoded) {
            this.decodeSegment(this.encodedString, this.fields);
            this.dirty = false;
            this.decoded = true;
        }
        if (this.fields.containsKey(fieldName)) {
            return this.fields.get(fieldName).getValue();
        }
        else {
            throw new InvalidFieldError("Invalid field: '" + fieldName + "'");
        }
    }
    setFieldValue(fieldName, value) {
        if (!this.decoded) {
            this.decodeSegment(this.encodedString, this.fields);
            this.dirty = false;
            this.decoded = true;
        }
        if (this.fields.containsKey(fieldName)) {
            this.fields.get(fieldName).setValue(value);
            this.dirty = true;
        }
        else {
            throw new InvalidFieldError(fieldName + " not found");
        }
    }
    //Overriden
    toObj() {
        let obj = {};
        let fieldNames = this.getFieldNames();
        for (let i = 0; i < fieldNames.length; i++) {
            let fieldName = fieldNames[i];
            let value = this.getFieldValue(fieldName);
            obj[fieldName] = value;
        }
        return obj;
    }
    encode() {
        if (this.encodedString == null || this.encodedString.length === 0 || this.dirty) {
            this.validate();
            this.encodedString = this.encodeSegment(this.fields);
            this.dirty = false;
            this.decoded = true;
        }
        return this.encodedString;
    }
    decode(encodedString) {
        this.encodedString = encodedString;
        this.dirty = false;
        this.decoded = false;
    }
}
