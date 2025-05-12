export interface EncodableSection {
    getId(): number;
    getName(): string;
    hasField(fieldName: string): boolean;
    getFieldValue(fieldName: string): any;
    setFieldValue(fieldName: string, value: any): void;
    toObj(): any;
    encode(): string;
    decode(encodedString: string): void;
    setIsDirty(status: boolean): void;
}
