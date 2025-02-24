export class RangeEntry {
    key;
    type;
    ids;
    constructor(key, type, ids) {
        this.key = key;
        this.type = type;
        this.ids = ids;
    }
    getKey() {
        return this.key;
    }
    setKey(key) {
        this.key = key;
    }
    getType() {
        return this.type;
    }
    setType(type) {
        this.type = type;
    }
    getIds() {
        return this.ids;
    }
    setIds(ids) {
        this.ids = ids;
    }
}
