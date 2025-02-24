/**
 * IntMap - A map of abstract type (defined by implementer) that is keyed by an
 * integer string id. Example `IntMap<number>`:
 * ```
 * const myIntMapOfNumbers: IntMap<number> = {
 *   "1":2,
 *   "3":4,
 * };
 * ```
 */
export interface IntMap<T> {
    [id: string]: T;
}
