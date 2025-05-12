/**
 * class for encoding errors
 *
 * @extends {Error}
 */
declare class EncodingError extends Error {
    /**
     * constructor - constructs an EncodingError
     *
     * @param {string} msg - Encoding Error Message
     * @return {undefined}
     */
    constructor(msg: string);
}
export { EncodingError };
