import { DecodingError } from "../../error/DecodingError.js";
import { EncodingError } from "../../error/EncodingError.js";
export class FixedIntegerEncoder {
    static encode(value, bitStringLength) {
        //let bitString = value.toString(2);
        let bin = [];
        if (value >= 1) {
            bin.push(1);
            while (value >= bin[0] * 2) {
                bin.unshift(bin[0] * 2);
            }
        }
        let bitString = "";
        for (let i = 0; i < bin.length; i++) {
            let b = bin[i];
            if (value >= b) {
                bitString += "1";
                value -= b;
            }
            else {
                bitString += "0";
            }
        }
        if (bitString.length > bitStringLength) {
            throw new EncodingError("Numeric value '" + value + "' is too large for a bit string length of '" + bitStringLength + "'");
        }
        while (bitString.length < bitStringLength) {
            bitString = "0" + bitString;
        }
        return bitString;
    }
    static decode(bitString) {
        if (!/^[0-1]*$/.test(bitString)) {
            throw new DecodingError("Undecodable FixedInteger '" + bitString + "'");
        }
        //return parseInt(bitString, 2);
        let value = 0;
        let bin = [];
        for (let i = 0; i < bitString.length; i++) {
            if (i === 0) {
                bin[bitString.length - (i + 1)] = 1;
            }
            else {
                bin[bitString.length - (i + 1)] = bin[bitString.length - i] * 2;
            }
        }
        for (let i = 0; i < bitString.length; i++) {
            if (bitString.charAt(i) === "1") {
                value += bin[i];
            }
        }
        return value;
    }
}
