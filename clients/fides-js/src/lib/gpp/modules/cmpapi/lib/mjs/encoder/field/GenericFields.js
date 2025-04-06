export class GenericFields {
    fields = new Map();
    containsKey(key) {
        return this.fields.has(key);
    }
    put(key, value) {
        this.fields.set(key, value);
    }
    get(key) {
        return this.fields.get(key);
    }
    getAll() {
        return new Map(this.fields);
    }
    reset(fields) {
        this.fields.clear();
        fields.getAll().forEach((value, key) => {
            this.fields.set(key, value);
        });
    }
}
