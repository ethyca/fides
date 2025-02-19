export class PingData {
    gppVersion;
    cmpStatus;
    cmpDisplayStatus;
    signalStatus;
    supportedAPIs;
    cmpId;
    sectionList;
    applicableSections;
    gppString;
    parsedSections;
    constructor(cmpApiContext) {
        this.gppVersion = cmpApiContext.gppVersion;
        this.cmpStatus = cmpApiContext.cmpStatus;
        this.cmpDisplayStatus = cmpApiContext.cmpDisplayStatus;
        this.signalStatus = cmpApiContext.signalStatus;
        this.supportedAPIs = cmpApiContext.supportedAPIs;
        this.cmpId = cmpApiContext.cmpId;
        this.sectionList = cmpApiContext.gppModel.getSectionIds();
        this.applicableSections = cmpApiContext.applicableSections;
        this.gppString = cmpApiContext.gppModel.encode();
        this.parsedSections = cmpApiContext.gppModel.toObject();
    }
}
