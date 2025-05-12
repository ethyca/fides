export interface Predicate<T> {
    test(t: T): boolean;
}
