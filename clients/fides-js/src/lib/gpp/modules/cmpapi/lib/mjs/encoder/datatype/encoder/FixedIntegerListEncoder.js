import { DecodingError } from "../../error/DecodingError.js";
import { EncodingError } from "../../error/EncodingError.js";
import { FixedIntegerEncoder } from "./FixedIntegerEncoder.js";
export class FixedIntegerListEncoder {
    static encode(value, elementBitStringLength, numElements) {
        if (value.length > numElements) {
            throw new EncodingError("Too many values '" + value.length + "'");
        }
        let bitString = "";
        for (let i = 0; i < value.length; i++) {
            bitString += FixedIntegerEncoder.encode(value[i], elementBitStringLength);
        }
        while (bitString.length < elementBitStringLength * numElements) {
            bitString += "0";
        }
        return bitString;
    }
    static decode(bitString, elementBitStringLength, numElements) {
        if (!/^[0-1]*$/.test(bitString)) {
            throw new DecodingError("Undecodable FixedInteger '" + bitString + "'");
        }
        if (bitString.length > elementBitStringLength * numElements) {
            throw new DecodingError("Undecodable FixedIntegerList '" + bitString + "'");
        }
        if (bitString.length % elementBitStringLength != 0) {
            throw new DecodingError("Undecodable FixedIntegerList '" + bitString + "'");
        }
        while (bitString.length < elementBitStringLength * numElements) {
            bitString += "0";
        }
        if (bitString.length > elementBitStringLength * numElements) {
            bitString = bitString.substring(0, elementBitStringLength * numElements);
        }
        let value = [];
        for (let i = 0; i < bitString.length; i += elementBitStringLength) {
            value.push(FixedIntegerEncoder.decode(bitString.substring(i, i + elementBitStringLength)));
        }
        while (value.length < numElements) {
            value.push(0);
        }
        return value;
    }
}
