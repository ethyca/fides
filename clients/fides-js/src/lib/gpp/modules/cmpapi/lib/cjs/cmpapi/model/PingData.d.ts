import { CmpApiContext } from "../CmpApiContext.js";
import { CmpStatus } from "../status/CmpStatus.js";
import { CmpDisplayStatus } from "../status/CmpDisplayStatus.js";
import { SignalStatus } from "../status/SignalStatus.js";
export declare class PingData {
    gppVersion: string;
    cmpStatus: CmpStatus;
    cmpDisplayStatus: CmpDisplayStatus;
    signalStatus: SignalStatus;
    supportedAPIs: string[];
    cmpId: number;
    sectionList: number[];
    applicableSections: number[];
    gppString: string;
    parsedSections: any;
    constructor(cmpApiContext: CmpApiContext);
}
