import { CustomCommands } from "./cmpapi/CustomCommands.js";
import { CmpStatus } from "./cmpapi/status/CmpStatus.js";
import { CmpDisplayStatus } from "./cmpapi/status/CmpDisplayStatus.js";
import { EventStatus } from "./cmpapi/status/EventStatus.js";
import { GVL, GVLUrlConfig } from "./GVL.js";
import { VendorList } from "./gvl/gvlmodel/VendorList.js";
import { SignalStatus } from "./cmpapi/status/SignalStatus.js";
export declare class CmpApi {
    private callResponder;
    private cmpApiContext;
    /**
     * @param {number} cmpId - IAB assigned CMP ID
     * @param {number} cmpVersion - integer version of the CMP
     * @param {CustomCommands} [customCommands] - custom commands from the cmp
     */
    constructor(cmpId: number, cmpVersion: number, customCommands?: CustomCommands);
    fireEvent(eventName: string, value: any): void;
    fireErrorEvent(value: string): void;
    fireSectionChange(value: string): void;
    getEventStatus(): EventStatus;
    setEventStatus(eventStatus: EventStatus): void;
    getCmpStatus(): CmpStatus;
    setCmpStatus(cmpStatus: CmpStatus): void;
    getCmpDisplayStatus(): CmpDisplayStatus;
    setCmpDisplayStatus(cmpDisplayStatus: CmpDisplayStatus): void;
    getSignalStatus(): SignalStatus;
    setSignalStatus(signalStatus: SignalStatus): void;
    getApplicableSections(): number[];
    setApplicableSections(applicableSections: number[]): void;
    getSupportedAPIs(): string[];
    setSupportedAPIs(supportedAPIs: string[]): void;
    setGppString(encodedGppString: string): void;
    getGppString(): string;
    setSectionString(sectionName: string, encodedSectionString: string): void;
    setSectionStringById(sectionId: number, encodedSectionString: string): void;
    getSectionString(sectionName: string): string;
    getSectionStringById(sectionId: number): string;
    setFieldValue(sectionName: string, fieldName: string, value: any): void;
    setFieldValueBySectionId(sectionId: number, fieldName: string, value: any): void;
    getFieldValue(sectionName: string, fieldName: string): any;
    getFieldValueBySectionId(sectionId: number, fieldName: string): any;
    getSection(sectionName: string): any;
    getSectionById(sectionId: number): any;
    hasSection(sectionName: string): any;
    hasSectionId(sectionId: number): any;
    deleteSection(sectionName: string): void;
    deleteSectionById(sectionId: number): void;
    clear(): void;
    getObject(): {};
    getGvlFromVendorList(vendorList: VendorList): GVL;
    getGvlFromUrl(gvlUrlConfig: GVLUrlConfig): Promise<GVL>;
}
