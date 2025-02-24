import { FibonacciIntegerEncoder } from "./encoder/FibonacciIntegerEncoder.js";
import { AbstractEncodableBitStringDataType } from "./AbstractEncodableBitStringDataType.js";
import { EncodingError } from "../error/EncodingError.js";
import { DecodingError } from "../error/DecodingError.js";
import { SubstringError } from "./SubstringError.js";
import { StringUtil } from "../util/index.js";
export class EncodableFibonacciInteger extends AbstractEncodableBitStringDataType {
    constructor(value, hardFailIfMissing = true) {
        super(hardFailIfMissing);
        this.setValue(value);
    }
    encode() {
        try {
            return FibonacciIntegerEncoder.encode(this.value);
        }
        catch (e) {
            throw new EncodingError(e);
        }
    }
    decode(bitString) {
        try {
            this.value = FibonacciIntegerEncoder.decode(bitString);
        }
        catch (e) {
            throw new DecodingError(e);
        }
    }
    substring(bitString, fromIndex) {
        try {
            let index = bitString.indexOf("11", fromIndex);
            if (index > 0) {
                return StringUtil.substring(bitString, fromIndex, index + 2);
            }
            else {
                return bitString;
            }
        }
        catch (e) {
            throw new SubstringError(e);
        }
    }
}
