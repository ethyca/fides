export declare abstract class AbstractBase64UrlEncoder {
    protected abstract pad(bitString: string): string;
    /**
     * Base 64 URL character set.  Different from standard Base64 char set
     * in that '+' and '/' are replaced with '-' and '_'.
     */
    private static DICT;
    private static REVERSE_DICT;
    encode(bitString: string): string;
    decode(str: string): string;
}
