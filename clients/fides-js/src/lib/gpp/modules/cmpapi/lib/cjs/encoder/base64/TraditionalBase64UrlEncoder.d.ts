import { AbstractBase64UrlEncoder } from "./AbstractBase64UrlEncoder.js";
export declare class TraditionalBase64UrlEncoder extends AbstractBase64UrlEncoder {
    private static instance;
    private constructor();
    static getInstance(): TraditionalBase64UrlEncoder;
    protected pad(bitString: string): string;
}
