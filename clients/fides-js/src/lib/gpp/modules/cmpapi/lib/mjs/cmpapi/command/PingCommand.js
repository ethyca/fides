import { PingData } from "../model/PingData.js";
import { Command } from "./Command.js";
export class PingCommand extends Command {
    respond() {
        let pingReturn = new PingData(this.cmpApiContext);
        this.invokeCallback(pingReturn);
    }
}
