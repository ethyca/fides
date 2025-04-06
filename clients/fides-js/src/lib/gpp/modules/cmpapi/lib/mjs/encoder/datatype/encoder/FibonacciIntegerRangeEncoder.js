import { FibonacciIntegerEncoder } from "./FibonacciIntegerEncoder.js";
import { BooleanEncoder } from "./BooleanEncoder.js";
import { FixedIntegerEncoder } from "./FixedIntegerEncoder.js";
import { DecodingError } from "../../error/DecodingError.js";
export class FibonacciIntegerRangeEncoder {
    static encode(value) {
        value = value.sort((n1, n2) => n1 - n2);
        let groups = [];
        let offset = 0;
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
            if (groups[i].length == 1) {
                let v = groups[i][0] - offset;
                offset = groups[i][0];
                bitString += "0" + FibonacciIntegerEncoder.encode(v);
            }
            else {
                let startVal = groups[i][0] - offset;
                offset = groups[i][0];
                let endVal = groups[i][groups[i].length - 1] - offset;
                offset = groups[i][groups[i].length - 1];
                bitString += "1" + FibonacciIntegerEncoder.encode(startVal) + FibonacciIntegerEncoder.encode(endVal);
            }
        }
        return bitString;
    }
    static decode(bitString) {
        if (!/^[0-1]*$/.test(bitString) || bitString.length < 12) {
            throw new DecodingError("Undecodable FibonacciIntegerRange '" + bitString + "'");
        }
        let value = [];
        let count = FixedIntegerEncoder.decode(bitString.substring(0, 12));
        let offset = 0;
        let startIndex = 12;
        for (let i = 0; i < count; i++) {
            let group = BooleanEncoder.decode(bitString.substring(startIndex, startIndex + 1));
            startIndex++;
            if (group === true) {
                let index = bitString.indexOf("11", startIndex);
                let start = FibonacciIntegerEncoder.decode(bitString.substring(startIndex, index + 2)) + offset;
                offset = start;
                startIndex = index + 2;
                index = bitString.indexOf("11", startIndex);
                let end = FibonacciIntegerEncoder.decode(bitString.substring(startIndex, index + 2)) + offset;
                offset = end;
                startIndex = index + 2;
                for (let j = start; j <= end; j++) {
                    value.push(j);
                }
            }
            else {
                let index = bitString.indexOf("11", startIndex);
                let val = FibonacciIntegerEncoder.decode(bitString.substring(startIndex, index + 2)) + offset;
                offset = val;
                value.push(val);
                startIndex = index + 2;
            }
        }
        return value;
    }
}
