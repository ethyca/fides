"use strict";Object.defineProperty(exports,"__esModule",{value:!0}),exports.HasSectionCommand=void 0;const Command_js_1=require("./Command.js");class HasSectionCommand extends Command_js_1.Command{respond(){if(!this.parameter||0===this.parameter.length)throw new Error("<section>[.version] parameter required");let e=this.cmpApiContext.gppModel.hasSection(this.parameter);this.invokeCallback(e)}}exports.HasSectionCommand=HasSectionCommand;