import { EncodableSection } from "./section/EncodableSection.js";
export declare class GppModel {
    private sections;
    private encodedString;
    private decoded;
    private dirty;
    constructor(encodedString?: string | null);
    setFieldValue(sectionName: string, fieldName: string, value: any): void;
    setFieldValueBySectionId(sectionId: number, fieldName: string, value: any): void;
    getFieldValue(sectionName: string, fieldName: string): any;
    getFieldValueBySectionId(sectionId: number, fieldName: string): any;
    hasField(sectionName: string, fieldName: string): boolean;
    hasFieldBySectionId(sectionId: number, fieldName: string): boolean;
    hasSection(sectionName: string): boolean;
    hasSectionId(sectionId: number): boolean;
    deleteSection(sectionName: string): void;
    deleteSectionById(sectionId: number): void;
    clear(): void;
    getHeader(): any;
    getSection(sectionName: string): any;
    getSectionIds(): any[];
    protected encodeModel(sections: Map<string, EncodableSection>): string;
    protected decodeModel(str: string): Map<string, EncodableSection>;
    encodeSection(sectionName: string): string;
    encodeSectionById(sectionId: number): string;
    decodeSection(sectionName: string, encodedString: string): void;
    decodeSectionById(sectionId: number, encodedString: string): void;
    toObject(): {};
    encode(): string;
    decode(encodedString: string | null): void;
}
