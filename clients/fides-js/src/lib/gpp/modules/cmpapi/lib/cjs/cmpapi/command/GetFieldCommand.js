"use strict";Object.defineProperty(exports,"__esModule",{value:!0}),exports.GetFieldCommand=void 0;const Command_js_1=require("./Command.js");class GetFieldCommand extends Command_js_1.Command{respond(){if(!this.parameter||0===this.parameter.length)throw new Error("<section>.<field> parameter required");let e=this.parameter.split(".");if(2!=e.length)throw new Error("Field name must be in the format <section>.<fieldName>");let t=e[0],r=e[1],i=this.cmpApiContext.gppModel.getFieldValue(t,r);this.invokeCallback(i)}}exports.GetFieldCommand=GetFieldCommand;