import { FibonacciIntegerRangeEncoder } from "./encoder/FibonacciIntegerRangeEncoder.js";
import { FixedIntegerEncoder } from "./encoder/FixedIntegerEncoder.js";
import { AbstractEncodableBitStringDataType } from "./AbstractEncodableBitStringDataType.js";
import { EncodingError } from "../error/EncodingError.js";
import { DecodingError } from "../error/DecodingError.js";
import { SubstringError } from "./SubstringError.js";
import { StringUtil } from "../util/index.js";
export class EncodableFibonacciIntegerRange extends AbstractEncodableBitStringDataType {
    constructor(value, hardFailIfMissing = true) {
        super(hardFailIfMissing);
        this.setValue(value);
    }
    encode() {
        try {
            return FibonacciIntegerRangeEncoder.encode(this.value);
        }
        catch (e) {
            throw new EncodingError(e);
        }
    }
    decode(bitString) {
        try {
            this.value = FibonacciIntegerRangeEncoder.decode(bitString);
        }
        catch (e) {
            throw new DecodingError(e);
        }
    }
    substring(bitString, fromIndex) {
        try {
            //TODO: add some validation
            let count = FixedIntegerEncoder.decode(StringUtil.substring(bitString, fromIndex, fromIndex + 12));
            let index = fromIndex + 12;
            for (let i = 0; i < count; i++) {
                if (bitString.charAt(index) === "1") {
                    index = bitString.indexOf("11", bitString.indexOf("11", index + 1) + 2) + 2;
                }
                else {
                    index = bitString.indexOf("11", index + 1) + 2;
                }
            }
            return StringUtil.substring(bitString, fromIndex, index);
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
        super.setValue(Array.from(new Set(value)).sort((n1, n2) => n1 - n2));
    }
}
