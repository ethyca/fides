import { DecodingError } from "../../error/DecodingError.js";
import { FibonacciIntegerRangeEncoder } from "./FibonacciIntegerRangeEncoder.js";
import { FixedBitfieldEncoder } from "./FixedBitfieldEncoder.js";
import { FixedIntegerEncoder } from "./FixedIntegerEncoder.js";
export class OptimizedFibonacciRangeEncoder {
    static encode(value) {
        //TODO: encoding the range before choosing the shortest is inefficient. There is probably a way
        //to identify in advance which will be shorter based on the array length and values
        let max = value.length > 0 ? value[value.length - 1] : 0;
        let rangeBitString = FibonacciIntegerRangeEncoder.encode(value);
        let rangeLength = rangeBitString.length;
        let bitFieldLength = max;
        if (rangeLength <= bitFieldLength) {
            return FixedIntegerEncoder.encode(max, 16) + "1" + rangeBitString;
        }
        else {
            let bits = [];
            let index = 0;
            for (let i = 0; i < max; i++) {
                if (i == value[index] - 1) {
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
    static decode(bitString) {
        if (!/^[0-1]*$/.test(bitString) || bitString.length < 2 || bitString.indexOf("11") !== bitString.length - 2) {
            throw new DecodingError("Undecodable FibonacciInteger '" + bitString + "'");
        }
        if (bitString.charAt(16) === "1") {
            return FibonacciIntegerRangeEncoder.decode(bitString.substring(17));
        }
        else {
            let value = [];
            let bits = FixedBitfieldEncoder.decode(bitString.substring(17));
            for (let i = 0; i < bits.length; i++) {
                if (bits[i] === true) {
                    value.push(i + 1);
                }
            }
            return value;
        }
    }
}
