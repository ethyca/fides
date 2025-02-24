export class UnencodableCharacter {
    validator;
    value = null;
    constructor(value, validator) {
        if (validator) {
            this.validator = validator;
        }
        else {
            this.validator = new (class {
                test(v) {
                    return true;
                }
            })();
        }
        this.setValue(value);
    }
    hasValue() {
        return this.value != null;
    }
    getValue() {
        return this.value;
    }
    setValue(value) {
        if (value) {
            this.value = value.charAt(0);
        }
        else {
            value = null;
        }
    }
}
