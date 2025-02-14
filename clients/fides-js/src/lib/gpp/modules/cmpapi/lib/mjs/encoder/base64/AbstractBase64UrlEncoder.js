import { FixedIntegerEncoder } from "../datatype/encoder/FixedIntegerEncoder.js";
import { DecodingError } from "../error/DecodingError.js";
import { EncodingError } from "../error/EncodingError.js";
export class AbstractBase64UrlEncoder {
    /**
     * Base 64 URL character set.  Different from standard Base64 char set
     * in that '+' and '/' are replaced with '-' and '_'.
     */
    static DICT = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";
    // prettier-ignore
    static REVERSE_DICT = new Map([
        ['A', 0], ['B', 1], ['C', 2], ['D', 3], ['E', 4], ['F', 5], ['G', 6], ['H', 7],
        ['I', 8], ['J', 9], ['K', 10], ['L', 11], ['M', 12], ['N', 13], ['O', 14], ['P', 15],
        ['Q', 16], ['R', 17], ['S', 18], ['T', 19], ['U', 20], ['V', 21], ['W', 22], ['X', 23],
        ['Y', 24], ['Z', 25], ['a', 26], ['b', 27], ['c', 28], ['d', 29], ['e', 30], ['f', 31],
        ['g', 32], ['h', 33], ['i', 34], ['j', 35], ['k', 36], ['l', 37], ['m', 38], ['n', 39],
        ['o', 40], ['p', 41], ['q', 42], ['r', 43], ['s', 44], ['t', 45], ['u', 46], ['v', 47],
        ['w', 48], ['x', 49], ['y', 50], ['z', 51], ['0', 52], ['1', 53], ['2', 54], ['3', 55],
        ['4', 56], ['5', 57], ['6', 58], ['7', 59], ['8', 60], ['9', 61], ['-', 62], ['_', 63]
    ]);
    encode(bitString) {
        // should only be 0 or 1
        if (!/^[0-1]*$/.test(bitString)) {
            throw new EncodingError("Unencodable Base64Url '" + bitString + "'");
        }
        bitString = this.pad(bitString);
        let str = "";
        let index = 0;
        while (index <= bitString.length - 6) {
            let s = bitString.substring(index, index + 6);
            try {
                let n = FixedIntegerEncoder.decode(s);
                let c = AbstractBase64UrlEncoder.DICT.charAt(n);
                str += c;
                index += 6;
            }
            catch (e) {
                throw new EncodingError("Unencodable Base64Url '" + bitString + "'");
            }
        }
        return str;
    }
    decode(str) {
        // should contain only characters from the base64url set
        if (!/^[A-Za-z0-9\-_]*$/.test(str)) {
            throw new DecodingError("Undecodable Base64URL string '" + str + "'");
        }
        let bitString = "";
        for (let i = 0; i < str.length; i++) {
            let c = str.charAt(i);
            let n = AbstractBase64UrlEncoder.REVERSE_DICT.get(c);
            let s = FixedIntegerEncoder.encode(n, 6);
            bitString += s;
        }
        return bitString;
    }
}
