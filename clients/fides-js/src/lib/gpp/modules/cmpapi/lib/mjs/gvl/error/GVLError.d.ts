/**
 * class for General GVL Errors
 *
 * @extends {Error}
 */
declare class GVLError extends Error {
    /**
     * constructor - constructs a GVLError
     *
     * @param {string} msg - Error message to display
     * @return {undefined}
     */
    constructor(msg: string);
}
export { GVLError };
