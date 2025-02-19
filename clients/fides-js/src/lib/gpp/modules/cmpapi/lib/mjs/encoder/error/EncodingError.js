/**
 * class for encoding errors
 *
 * @extends {Error}
 */
class EncodingError extends Error {
    /**
     * constructor - constructs an EncodingError
     *
     * @param {string} msg - Encoding Error Message
     * @return {undefined}
     */
    constructor(msg) {
        super(msg);
        this.name = "EncodingError";
    }
}
export { EncodingError };
