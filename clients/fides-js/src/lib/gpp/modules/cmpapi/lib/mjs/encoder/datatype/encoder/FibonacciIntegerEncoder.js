import { DecodingError } from "../../error/DecodingError.js";
export class FibonacciIntegerEncoder {
    static encode(value) {
        let fib = [];
        if (value >= 1) {
            fib.push(1);
            if (value >= 2) {
                fib.push(2);
                let i = 2;
                while (value >= fib[i - 1] + fib[i - 2]) {
                    fib.push(fib[i - 1] + fib[i - 2]);
                    i++;
                }
            }
        }
        let bitString = "1";
        for (let i = fib.length - 1; i >= 0; i--) {
            let f = fib[i];
            if (value >= f) {
                bitString = "1" + bitString;
                value -= f;
            }
            else {
                bitString = "0" + bitString;
            }
        }
        return bitString;
    }
    static decode(bitString) {
        if (!/^[0-1]*$/.test(bitString) || bitString.length < 2 || bitString.indexOf("11") !== bitString.length - 2) {
            throw new DecodingError("Undecodable FibonacciInteger '" + bitString + "'");
        }
        let value = 0;
        let fib = [];
        for (let i = 0; i < bitString.length - 1; i++) {
            if (i === 0) {
                fib.push(1);
            }
            else if (i === 1) {
                fib.push(2);
            }
            else {
                fib.push(fib[i - 1] + fib[i - 2]);
            }
        }
        for (let i = 0; i < bitString.length - 1; i++) {
            if (bitString.charAt(i) === "1") {
                value += fib[i];
            }
        }
        return value;
    }
}
