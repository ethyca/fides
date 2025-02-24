import { DecodingError } from "../error/DecodingError.js";
export class BitStringEncoder {
    static instance = new BitStringEncoder();
    constructor() { }
    static getInstance() {
        return this.instance;
    }
    encode(fields, fieldNames) {
        let bitString = "";
        for (let i = 0; i < fieldNames.length; i++) {
            let fieldName = fieldNames[i];
            if (fields.containsKey(fieldName)) {
                let field = fields.get(fieldName);
                bitString += field.encode();
            }
            else {
                throw new Error("Field not found: '" + fieldName + "'");
            }
        }
        return bitString;
    }
    decode(bitString, fieldNames, fields) {
        let index = 0;
        for (let i = 0; i < fieldNames.length; i++) {
            let fieldName = fieldNames[i];
            if (fields.containsKey(fieldName)) {
                let field = fields.get(fieldName);
                try {
                    let substring = field.substring(bitString, index);
                    field.decode(substring);
                    index += substring.length;
                }
                catch (e) {
                    if (e.name === "SubstringError" && !field.getHardFailIfMissing()) {
                        return;
                    }
                    else {
                        throw new DecodingError("Unable to decode field '" + fieldName + "'");
                    }
                }
            }
            else {
                throw new Error("Field not found: '" + fieldName + "'");
            }
        }
    }
}
