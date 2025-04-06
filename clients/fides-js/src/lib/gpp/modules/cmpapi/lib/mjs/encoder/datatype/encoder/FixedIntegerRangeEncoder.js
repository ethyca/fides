import { DecodingError } from "../../error/DecodingError.js";
import { BooleanEncoder } from "./BooleanEncoder.js";
import { FixedIntegerEncoder } from "./FixedIntegerEncoder.js";
export class FixedIntegerRangeEncoder {
    static encode(value) {
        value.sort((n1, n2) => n1 - n2);
        let groups = [];
        let groupStartIndex = 0;
        while (groupStartIndex < value.length) {
            let groupEndIndex = groupStartIndex;
            while (groupEndIndex < value.length - 1 && value[groupEndIndex] + 1 === value[groupEndIndex + 1]) {
                groupEndIndex++;
            }
            groups.push(value.slice(groupStartIndex, groupEndIndex + 1));
            groupStartIndex = groupEndIndex + 1;
        }
        let bitString = FixedIntegerEncoder.encode(groups.length, 12);
        for (let i = 0; i < groups.length; i++) {
            if (groups[i].length === 1) {
                bitString += "0" + FixedIntegerEncoder.encode(groups[i][0], 16);
            }
            else {
                bitString +=
                    "1" +
                        FixedIntegerEncoder.encode(groups[i][0], 16) +
                        FixedIntegerEncoder.encode(groups[i][groups[i].length - 1], 16);
            }
        }
        return bitString;
    }
    static decode(bitString) {
        if (!/^[0-1]*$/.test(bitString) || bitString.length < 12) {
            throw new DecodingError("Undecodable FixedIntegerRange '" + bitString + "'");
        }
        let value = [];
        let count = FixedIntegerEncoder.decode(bitString.substring(0, 12));
        let startIndex = 12;
        for (let i = 0; i < count; i++) {
            let group = BooleanEncoder.decode(bitString.substring(startIndex, startIndex + 1));
            startIndex++;
            if (group === true) {
                let start = FixedIntegerEncoder.decode(bitString.substring(startIndex, startIndex + 16));
                startIndex += 16;
                let end = FixedIntegerEncoder.decode(bitString.substring(startIndex, startIndex + 16));
                startIndex += 16;
                for (let j = start; j <= end; j++) {
                    value.push(j);
                }
            }
            else {
                let val = FixedIntegerEncoder.decode(bitString.substring(startIndex, startIndex + 16));
                value.push(val);
                startIndex += 16;
            }
        }
        return value;
    }
}
