import { AbstractBase64UrlEncoder } from "./AbstractBase64UrlEncoder.js";
export declare class CompressedBase64UrlEncoder extends AbstractBase64UrlEncoder {
    private static instance;
    private constructor();
    static getInstance(): CompressedBase64UrlEncoder;
    protected pad(bitString: string): string;
}
