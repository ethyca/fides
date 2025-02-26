import { CmpStatus } from "./status/CmpStatus.js";
import { CmpDisplayStatus } from "./status/CmpDisplayStatus.js";
import { EventListenerQueue } from "./EventListenerQueue.js";
import { GppModel } from "../encoder/GppModel.js";
import { SignalStatus } from "./status/SignalStatus.js";
/**
 * Class holds shareable data across cmp api and provides change event listener for GppModel.
 * Within the context of the CmpApi, this class acts much like a global state or database,
 * where CmpApi sets data and Commands read the data.
 */
export class CmpApiContext {
    gppVersion = "1.1";
    supportedAPIs = [];
    eventQueue = new EventListenerQueue(this);
    cmpStatus = CmpStatus.LOADING;
    cmpDisplayStatus = CmpDisplayStatus.HIDDEN;
    signalStatus = SignalStatus.NOT_READY;
    applicableSections = [];
    gppModel = new GppModel();
    cmpId;
    cmpVersion;
    eventStatus;
    reset() {
        this.eventQueue.clear();
        this.cmpStatus = CmpStatus.LOADING;
        this.cmpDisplayStatus = CmpDisplayStatus.HIDDEN;
        this.signalStatus = SignalStatus.NOT_READY;
        this.applicableSections = [];
        this.supportedAPIs = [];
        this.gppModel = new GppModel();
        delete this.cmpId;
        delete this.cmpVersion;
        delete this.eventStatus;
    }
}
