import { DecodingError } from "../../error/DecodingError.js";
import { FixedIntegerEncoder } from "./FixedIntegerEncoder.js";
export class DatetimeEncoder {
    static encode(value) {
        if (value) {
            return FixedIntegerEncoder.encode(Math.round(value.getTime() / 100), 36);
        }
        else {
            return FixedIntegerEncoder.encode(0, 36);
        }
    }
    static decode(bitString) {
        if (!/^[0-1]*$/.test(bitString) || bitString.length !== 36) {
            throw new DecodingError("Undecodable Datetime '" + bitString + "'");
        }
        return new Date(FixedIntegerEncoder.decode(bitString) * 100);
    }
}
