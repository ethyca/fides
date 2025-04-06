/**
 * class for decoding errors
 *
 * @extends {Error}
 */
declare class DecodingError extends Error {
    /**
     * constructor - constructs an DecodingError
     *
     * @param {string} msg - Decoding Error Message
     * @return {undefined}
     */
    constructor(msg: string);
}
export { DecodingError };
