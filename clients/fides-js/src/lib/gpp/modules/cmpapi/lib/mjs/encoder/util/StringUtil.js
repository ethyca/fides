import { SubstringError } from "../datatype/SubstringError.js";
export class StringUtil {
    /**
     * Throws a SubstringError if the indexes aren't within the length of the string
     */
    static substring(s, start, end) {
        if (end > s.length || start < 0 || start > end) {
            throw new SubstringError("Invalid substring indexes " + start + ":" + end + " for string of length " + s.length);
        }
        return s.substring(start, end);
    }
}
