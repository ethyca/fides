import { FixedBitfieldEncoder } from "./encoder/FixedBitfieldEncoder.js";
import { AbstractEncodableBitStringDataType } from "./AbstractEncodableBitStringDataType.js";
import { EncodingError } from "../error/EncodingError.js";
import { DecodingError } from "../error/DecodingError.js";
import { SubstringError } from "./SubstringError.js";
import { StringUtil } from "../util/StringUtil.js";
export class EncodableFlexibleBitfield extends AbstractEncodableBitStringDataType {
    getLength;
    constructor(getLength, value, hardFailIfMissing = true) {
        super(hardFailIfMissing);
        this.getLength = getLength;
        this.setValue(value);
    }
    encode() {
        try {
            return FixedBitfieldEncoder.encode(this.value, this.getLength());
        }
        catch (e) {
            throw new EncodingError(e);
        }
    }
    decode(bitString) {
        try {
            this.value = FixedBitfieldEncoder.decode(bitString);
        }
        catch (e) {
            throw new DecodingError(e);
        }
    }
    substring(bitString, fromIndex) {
        try {
            return StringUtil.substring(bitString, fromIndex, fromIndex + this.getLength());
        }
        catch (e) {
            throw new SubstringError(e);
        }
    }
    // Overriden
    getValue() {
        return [...super.getValue()];
    }
    // Overriden
    setValue(value) {
        let numElements = this.getLength();
        let v = [...value];
        for (let i = v.length; i < numElements; i++) {
            v.push(false);
        }
        if (v.length > numElements) {
            v = v.slice(0, numElements);
        }
        super.setValue([...v]);
    }
}
