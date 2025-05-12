import { DecodingError } from "../../error/DecodingError.js";
import { EncodingError } from "../../error/EncodingError.js";
export class BooleanEncoder {
    static encode(value) {
        if (value === true) {
            return "1";
        }
        else if (value === false) {
            return "0";
        }
        else {
            throw new EncodingError("Unencodable Boolean '" + value + "'");
        }
    }
    static decode(bitString) {
        if (bitString === "1") {
            return true;
        }
        else if (bitString === "0") {
            return false;
        }
        else {
            throw new DecodingError("Undecodable Boolean '" + bitString + "'");
        }
    }
}
