export interface Fields<T> {
    containsKey(key: string): boolean;
    put(key: string, value: T): void;
    get(key: string): T;
    getAll(): Map<string, T>;
    reset(fields: Fields<T>): void;
}
