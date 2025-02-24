import { DatetimeEncoder } from "./encoder/DatetimeEncoder.js";
import { AbstractEncodableBitStringDataType } from "./AbstractEncodableBitStringDataType.js";
import { EncodingError } from "../error/EncodingError.js";
import { DecodingError } from "../error/DecodingError.js";
import { SubstringError } from "./SubstringError.js";
import { StringUtil } from "../util/index.js";
export class EncodableDatetime extends AbstractEncodableBitStringDataType {
    constructor(value, hardFailIfMissing = true) {
        super(hardFailIfMissing);
        this.setValue(value);
    }
    encode() {
        try {
            return DatetimeEncoder.encode(this.value);
        }
        catch (e) {
            throw new EncodingError(e);
        }
    }
    decode(bitString) {
        try {
            this.value = DatetimeEncoder.decode(bitString);
        }
        catch (e) {
            throw new DecodingError(e);
        }
    }
    substring(bitString, fromIndex) {
        try {
            return StringUtil.substring(bitString, fromIndex, fromIndex + 36);
        }
        catch (e) {
            throw new SubstringError(e);
        }
    }
}
