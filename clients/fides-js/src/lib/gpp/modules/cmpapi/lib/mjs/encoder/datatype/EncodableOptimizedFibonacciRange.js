import { FibonacciIntegerRangeEncoder } from "./encoder/FibonacciIntegerRangeEncoder.js";
import { FixedBitfieldEncoder } from "./encoder/FixedBitfieldEncoder.js";
import { FixedIntegerEncoder } from "./encoder/FixedIntegerEncoder.js";
import { AbstractEncodableBitStringDataType } from "./AbstractEncodableBitStringDataType.js";
import { EncodableFibonacciIntegerRange } from "./EncodableFibonacciIntegerRange.js";
import { DecodingError } from "../error/DecodingError.js";
import { EncodingError } from "../error/EncodingError.js";
import { SubstringError } from "./SubstringError.js";
import { StringUtil } from "../util/StringUtil.js";
export class EncodableOptimizedFibonacciRange extends AbstractEncodableBitStringDataType {
    constructor(value, hardFailIfMissing = true) {
        super(hardFailIfMissing);
        this.setValue(value);
    }
    encode() {
        try {
            //TODO: encoding the range before choosing the shortest is inefficient. There is probably a way
            //to identify in advance which will be shorter based on the array length and values
            let max = this.value.length > 0 ? this.value[this.value.length - 1] : 0;
            let rangeBitString = FibonacciIntegerRangeEncoder.encode(this.value);
            let rangeLength = rangeBitString.length;
            let bitFieldLength = max;
            if (rangeLength <= bitFieldLength) {
                return FixedIntegerEncoder.encode(max, 16) + "1" + rangeBitString;
            }
            else {
                let bits = [];
                let index = 0;
                for (let i = 0; i < max; i++) {
                    if (i == this.value[index] - 1) {
                        bits[i] = true;
                        index++;
                    }
                    else {
                        bits[i] = false;
                    }
                }
                return FixedIntegerEncoder.encode(max, 16) + "0" + FixedBitfieldEncoder.encode(bits, bitFieldLength);
            }
        }
        catch (e) {
            throw new EncodingError(e);
        }
    }
    decode(bitString) {
        try {
            if (bitString.charAt(16) === "1") {
                this.value = FibonacciIntegerRangeEncoder.decode(bitString.substring(17));
            }
            else {
                let value = [];
                let bits = FixedBitfieldEncoder.decode(bitString.substring(17));
                for (let i = 0; i < bits.length; i++) {
                    if (bits[i] === true) {
                        value.push(i + 1);
                    }
                }
                this.value = value;
            }
        }
        catch (e) {
            throw new DecodingError(e);
        }
    }
    substring(bitString, fromIndex) {
        try {
            let max = FixedIntegerEncoder.decode(StringUtil.substring(bitString, fromIndex, fromIndex + 16));
            if (bitString.charAt(fromIndex + 16) === "1") {
                return (StringUtil.substring(bitString, fromIndex, fromIndex + 17) +
                    new EncodableFibonacciIntegerRange([]).substring(bitString, fromIndex + 17));
            }
            else {
                return StringUtil.substring(bitString, fromIndex, fromIndex + 17 + max);
            }
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
