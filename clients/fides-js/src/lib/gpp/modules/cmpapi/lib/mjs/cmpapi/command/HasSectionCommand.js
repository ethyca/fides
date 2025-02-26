import { Command } from "./Command.js";
export class HasSectionCommand extends Command {
    respond() {
        if (!this.parameter || this.parameter.length === 0) {
            throw new Error("<section>[.version] parameter required");
        }
        let hasSection = this.cmpApiContext.gppModel.hasSection(this.parameter);
        this.invokeCallback(hasSection);
    }
}
