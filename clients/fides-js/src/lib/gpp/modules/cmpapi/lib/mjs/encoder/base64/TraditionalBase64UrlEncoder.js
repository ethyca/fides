import { AbstractBase64UrlEncoder } from "./AbstractBase64UrlEncoder.js";
export class TraditionalBase64UrlEncoder extends AbstractBase64UrlEncoder {
    static instance = new TraditionalBase64UrlEncoder();
    constructor() {
        super();
    }
    static getInstance() {
        return this.instance;
    }
    // Overriden
    pad(bitString) {
        while (bitString.length % 24 > 0) {
            bitString += "0";
        }
        return bitString;
    }
}
