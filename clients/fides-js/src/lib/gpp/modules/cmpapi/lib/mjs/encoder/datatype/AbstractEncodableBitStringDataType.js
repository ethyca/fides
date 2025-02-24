import { ValidationError } from "../error/ValidationError.js";
export class AbstractEncodableBitStringDataType {
    // this if for backwards compatibility with the newer fields
    hardFailIfMissing;
    validator;
    value;
    constructor(hardFailIfMising = true) {
        this.hardFailIfMissing = hardFailIfMising;
    }
    withValidator(validator) {
        this.validator = validator;
        return this;
    }
    hasValue() {
        return this.value !== undefined && this.value !== null;
    }
    getValue() {
        return this.value;
    }
    setValue(value) {
        if (!this.validator || this.validator.test(value)) {
            this.value = value;
        }
        else {
            throw new ValidationError("Invalid value '" + value + "'");
        }
    }
    getHardFailIfMissing() {
        return this.hardFailIfMissing;
    }
}
