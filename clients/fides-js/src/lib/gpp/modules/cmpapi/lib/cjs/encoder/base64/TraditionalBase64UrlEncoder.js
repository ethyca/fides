"use strict";Object.defineProperty(exports,"__esModule",{value:!0}),exports.TraditionalBase64UrlEncoder=void 0;const AbstractBase64UrlEncoder_js_1=require("./AbstractBase64UrlEncoder.js");class TraditionalBase64UrlEncoder extends AbstractBase64UrlEncoder_js_1.AbstractBase64UrlEncoder{constructor(){super()}static getInstance(){return this.instance}pad(r){for(;r.length%24>0;)r+="0";return r}}exports.TraditionalBase64UrlEncoder=TraditionalBase64UrlEncoder,TraditionalBase64UrlEncoder.instance=new TraditionalBase64UrlEncoder;