import { FixedStringEncoder } from "./encoder/FixedStringEncoder.js";
import { AbstractEncodableBitStringDataType } from "./AbstractEncodableBitStringDataType.js";
import { EncodingError } from "../error/EncodingError.js";
import { DecodingError } from "../error/DecodingError.js";
import { SubstringError } from "./SubstringError.js";
import { StringUtil } from "../util/StringUtil.js";
export class EncodableFixedString extends AbstractEncodableBitStringDataType {
    stringLength;
    constructor(stringLength, value, hardFailIfMissing = true) {
        super(hardFailIfMissing);
        this.stringLength = stringLength;
        this.setValue(value);
    }
    encode() {
        try {
            return FixedStringEncoder.encode(this.value, this.stringLength);
        }
        catch (e) {
            throw new EncodingError(e);
        }
    }
    decode(bitString) {
        try {
            this.value = FixedStringEncoder.decode(bitString);
        }
        catch (e) {
            throw new DecodingError(e);
        }
    }
    substring(bitString, fromIndex) {
        try {
            return StringUtil.substring(bitString, fromIndex, fromIndex + this.stringLength * 6);
        }
        catch (e) {
            throw new SubstringError(e);
        }
    }
}
