export class ConsentLanguages {
    static langSet = new Set([
        "BG",
        "CA",
        "CS",
        "DA",
        "DE",
        "EL",
        "EN",
        "ES",
        "ET",
        "FI",
        "FR",
        "HR",
        "HU",
        "IT",
        "JA",
        "LT",
        "LV",
        "MT",
        "NL",
        "NO",
        "PL",
        "PT",
        "RO",
        "RU",
        "SK",
        "SL",
        "SV",
        "TR",
        "ZH",
    ]);
    has(key) {
        return ConsentLanguages.langSet.has(key);
    }
    forEach(callback) {
        ConsentLanguages.langSet.forEach(callback);
    }
    get size() {
        return ConsentLanguages.langSet.size;
    }
}
