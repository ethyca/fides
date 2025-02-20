import { CmpApiContext } from "./cmpapi/CmpApiContext.js";
import { CallResponder } from "./cmpapi/CallResponder.js";
import { GVL } from "./GVL.js";
import { Sections } from "./encoder/section/Sections.js";
export class CmpApi {
    callResponder;
    cmpApiContext;
    /**
     * @param {number} cmpId - IAB assigned CMP ID
     * @param {number} cmpVersion - integer version of the CMP
     * @param {CustomCommands} [customCommands] - custom commands from the cmp
     */
    constructor(cmpId, cmpVersion, customCommands) {
        this.cmpApiContext = new CmpApiContext();
        this.cmpApiContext.cmpId = cmpId;
        this.cmpApiContext.cmpVersion = cmpVersion;
        this.callResponder = new CallResponder(this.cmpApiContext, customCommands);
    }
    fireEvent(eventName, value) {
        this.cmpApiContext.eventQueue.exec(eventName, value);
    }
    fireErrorEvent(value) {
        this.cmpApiContext.eventQueue.exec("error", value);
    }
    fireSectionChange(value) {
        this.cmpApiContext.eventQueue.exec("sectionChange", value);
    }
    getEventStatus() {
        return this.cmpApiContext.eventStatus;
    }
    setEventStatus(eventStatus) {
        this.cmpApiContext.eventStatus = eventStatus;
    }
    getCmpStatus() {
        return this.cmpApiContext.cmpStatus;
    }
    setCmpStatus(cmpStatus) {
        this.cmpApiContext.cmpStatus = cmpStatus;
        this.cmpApiContext.eventQueue.exec("cmpStatus", cmpStatus);
    }
    getCmpDisplayStatus() {
        return this.cmpApiContext.cmpDisplayStatus;
    }
    setCmpDisplayStatus(cmpDisplayStatus) {
        this.cmpApiContext.cmpDisplayStatus = cmpDisplayStatus;
        this.cmpApiContext.eventQueue.exec("cmpDisplayStatus", cmpDisplayStatus);
    }
    getSignalStatus() {
        return this.cmpApiContext.signalStatus;
    }
    setSignalStatus(signalStatus) {
        this.cmpApiContext.signalStatus = signalStatus;
        this.cmpApiContext.eventQueue.exec("signalStatus", signalStatus);
    }
    getApplicableSections() {
        return this.cmpApiContext.applicableSections;
    }
    setApplicableSections(applicableSections) {
        this.cmpApiContext.applicableSections = applicableSections;
    }
    getSupportedAPIs() {
        return this.cmpApiContext.supportedAPIs;
    }
    setSupportedAPIs(supportedAPIs) {
        this.cmpApiContext.supportedAPIs = supportedAPIs;
    }
    setGppString(encodedGppString) {
        this.cmpApiContext.gppModel.decode(encodedGppString);
    }
    getGppString() {
        return this.cmpApiContext.gppModel.encode();
    }
    setSectionString(sectionName, encodedSectionString) {
        this.cmpApiContext.gppModel.decodeSection(sectionName, encodedSectionString);
    }
    setSectionStringById(sectionId, encodedSectionString) {
        this.setSectionString(Sections.SECTION_ID_NAME_MAP.get(sectionId), encodedSectionString);
    }
    getSectionString(sectionName) {
        return this.cmpApiContext.gppModel.encodeSection(sectionName);
    }
    getSectionStringById(sectionId) {
        return this.getSectionString(Sections.SECTION_ID_NAME_MAP.get(sectionId));
    }
    setFieldValue(sectionName, fieldName, value) {
        this.cmpApiContext.gppModel.setFieldValue(sectionName, fieldName, value);
    }
    setFieldValueBySectionId(sectionId, fieldName, value) {
        this.setFieldValue(Sections.SECTION_ID_NAME_MAP.get(sectionId), fieldName, value);
    }
    getFieldValue(sectionName, fieldName) {
        return this.cmpApiContext.gppModel.getFieldValue(sectionName, fieldName);
    }
    getFieldValueBySectionId(sectionId, fieldName) {
        return this.getFieldValue(Sections.SECTION_ID_NAME_MAP.get(sectionId), fieldName);
    }
    getSection(sectionName) {
        return this.cmpApiContext.gppModel.getSection(sectionName);
    }
    getSectionById(sectionId) {
        return this.getSection(Sections.SECTION_ID_NAME_MAP.get(sectionId));
    }
    hasSection(sectionName) {
        return this.cmpApiContext.gppModel.hasSection(sectionName);
    }
    hasSectionId(sectionId) {
        return this.hasSection(Sections.SECTION_ID_NAME_MAP.get(sectionId));
    }
    deleteSection(sectionName) {
        this.cmpApiContext.gppModel.deleteSection(sectionName);
    }
    deleteSectionById(sectionId) {
        this.deleteSection(Sections.SECTION_ID_NAME_MAP.get(sectionId));
    }
    clear() {
        this.cmpApiContext.gppModel.clear();
    }
    getObject() {
        return this.cmpApiContext.gppModel.toObject();
    }
    getGvlFromVendorList(vendorList) {
        return GVL.fromVendorList(vendorList);
    }
    async getGvlFromUrl(gvlUrlConfig) {
        return GVL.fromUrl(gvlUrlConfig);
    }
}
