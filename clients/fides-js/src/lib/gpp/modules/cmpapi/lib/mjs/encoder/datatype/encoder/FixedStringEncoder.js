import { DecodingError } from "../../error/DecodingError.js";
import { EncodingError } from "../../error/EncodingError.js";
import { FixedIntegerEncoder } from "./FixedIntegerEncoder.js";
export class FixedStringEncoder {
    static encode(value, stringLength) {
        while (value.length < stringLength) {
            value += " ";
        }
        let bitString = "";
        for (let i = 0; i < value.length; i++) {
            let code = value.charCodeAt(i);
            if (code === 32) {
                // space
                bitString += FixedIntegerEncoder.encode(63, 6);
            }
            else if (code >= 65) {
                bitString += FixedIntegerEncoder.encode(value.charCodeAt(i) - 65, 6);
            }
            else {
                throw new EncodingError("Unencodable FixedString '" + value + "'");
            }
        }
        return bitString;
    }
    static decode(bitString) {
        if (!/^[0-1]*$/.test(bitString) || bitString.length % 6 !== 0) {
            throw new DecodingError("Undecodable FixedString '" + bitString + "'");
        }
        let value = "";
        for (let i = 0; i < bitString.length; i += 6) {
            let code = FixedIntegerEncoder.decode(bitString.substring(i, i + 6));
            if (code === 63) {
                value += " ";
            }
            else {
                value += String.fromCharCode(code + 65);
            }
        }
        return value.trim();
    }
}
