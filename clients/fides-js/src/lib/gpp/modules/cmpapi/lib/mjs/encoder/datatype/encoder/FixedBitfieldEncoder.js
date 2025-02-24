import { DecodingError } from "../../error/DecodingError.js";
import { EncodingError } from "../../error/EncodingError.js";
import { BooleanEncoder } from "./BooleanEncoder.js";
export class FixedBitfieldEncoder {
    static encode(value, bitStringLength) {
        if (value.length > bitStringLength) {
            throw new EncodingError("Too many values '" + value.length + "'");
        }
        let bitString = "";
        for (let i = 0; i < value.length; i++) {
            bitString += BooleanEncoder.encode(value[i]);
        }
        while (bitString.length < bitStringLength) {
            bitString += "0";
        }
        return bitString;
    }
    static decode(bitString) {
        if (!/^[0-1]*$/.test(bitString)) {
            throw new DecodingError("Undecodable FixedBitfield '" + bitString + "'");
        }
        let value = [];
        for (let i = 0; i < bitString.length; i++) {
            value.push(BooleanEncoder.decode(bitString.substring(i, i + 1)));
        }
        return value;
    }
}
