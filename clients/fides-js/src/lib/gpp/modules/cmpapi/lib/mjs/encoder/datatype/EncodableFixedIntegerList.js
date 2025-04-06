import { FixedIntegerListEncoder } from "./encoder/FixedIntegerListEncoder.js";
import { AbstractEncodableBitStringDataType } from "./AbstractEncodableBitStringDataType.js";
import { EncodingError } from "../error/EncodingError.js";
import { DecodingError } from "../error/DecodingError.js";
import { SubstringError } from "./SubstringError.js";
import { StringUtil } from "../util/StringUtil.js";
export class EncodableFixedIntegerList extends AbstractEncodableBitStringDataType {
    elementBitStringLength;
    numElements;
    constructor(elementBitStringLength, value, hardFailIfMissing = true) {
        super(hardFailIfMissing);
        this.elementBitStringLength = elementBitStringLength;
        this.numElements = value.length;
        this.setValue(value);
    }
    encode() {
        try {
            return FixedIntegerListEncoder.encode(this.value, this.elementBitStringLength, this.numElements);
        }
        catch (e) {
            throw new EncodingError(e);
        }
    }
    decode(bitString) {
        try {
            this.value = FixedIntegerListEncoder.decode(bitString, this.elementBitStringLength, this.numElements);
        }
        catch (e) {
            throw new DecodingError(e);
        }
    }
    substring(bitString, fromIndex) {
        try {
            return StringUtil.substring(bitString, fromIndex, fromIndex + this.elementBitStringLength * this.numElements);
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
        let v = [...value];
        for (let i = v.length; i < this.numElements; i++) {
            v.push(0);
        }
        if (v.length > this.numElements) {
            v = v.slice(0, this.numElements);
        }
        super.setValue(v);
    }
}
