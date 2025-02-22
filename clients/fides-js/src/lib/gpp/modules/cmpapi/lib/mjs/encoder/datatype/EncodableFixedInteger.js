import { FixedIntegerEncoder } from "./encoder/FixedIntegerEncoder.js";
import { AbstractEncodableBitStringDataType } from "./AbstractEncodableBitStringDataType.js";
import { EncodingError } from "../error/EncodingError.js";
import { DecodingError } from "../error/DecodingError.js";
import { SubstringError } from "./SubstringError.js";
import { StringUtil } from "../util/StringUtil.js";
export class EncodableFixedInteger extends AbstractEncodableBitStringDataType {
    bitStringLength;
    constructor(bitStringLength, value, hardFailIfMissing = true) {
        super(hardFailIfMissing);
        this.bitStringLength = bitStringLength;
        this.setValue(value);
    }
    encode() {
        try {
            return FixedIntegerEncoder.encode(this.value, this.bitStringLength);
        }
        catch (e) {
            throw new EncodingError(e);
        }
    }
    decode(bitString) {
        try {
            this.value = FixedIntegerEncoder.decode(bitString);
        }
        catch (e) {
            throw new DecodingError(e);
        }
    }
    substring(bitString, fromIndex) {
        try {
            return StringUtil.substring(bitString, fromIndex, fromIndex + this.bitStringLength);
        }
        catch (e) {
            throw new SubstringError(e);
        }
    }
}
