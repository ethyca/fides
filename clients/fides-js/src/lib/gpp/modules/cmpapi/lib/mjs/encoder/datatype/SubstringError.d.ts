import { DecodingError } from "../error/DecodingError.js";
/**
 * class for decoding errors
 *
 * @extends {DecodingError}
 */
declare class SubstringError extends DecodingError {
    /**
     * constructor - constructs an DecodingError
     *
     * @param {string} msg - Decoding Error Message
     * @return {undefined}
     */
    constructor(msg: string);
}
export { SubstringError };
