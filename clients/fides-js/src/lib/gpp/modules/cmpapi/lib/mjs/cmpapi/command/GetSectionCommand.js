import { Command } from "./Command.js";
export class GetSectionCommand extends Command {
    respond() {
        if (!this.parameter || this.parameter.length === 0) {
            throw new Error("<section> parameter required");
        }
        let section = null;
        if (this.cmpApiContext.gppModel.hasSection(this.parameter)) {
            section = this.cmpApiContext.gppModel.getSection(this.parameter);
        }
        this.invokeCallback(section);
    }
}
