"use strict";Object.defineProperty(exports,"__esModule",{value:!0}),exports.UspV1=void 0;const UspV1CoreSegment_js_1=require("../segment/UspV1CoreSegment.js"),AbstractLazilyEncodableSection_js_1=require("./AbstractLazilyEncodableSection.js");class UspV1 extends AbstractLazilyEncodableSection_js_1.AbstractLazilyEncodableSection{constructor(e){super(),e&&e.length>0&&this.decode(e)}getId(){return UspV1.ID}getName(){return UspV1.NAME}getVersion(){return UspV1.VERSION}initializeSegments(){let e=[];return e.push(new UspV1CoreSegment_js_1.UspV1CoreSegment),e}decodeSection(e){let t=this.initializeSegments();if(null!=e&&0!==e.length){let s=e.split(".");for(let e=0;e<t.length;e++)s.length>e&&t[e].decode(s[e])}return t}encodeSection(e){let t=[];for(let s=0;s<e.length;s++){let n=e[s];t.push(n.encode())}return t.join(".")}}exports.UspV1=UspV1,UspV1.ID=6,UspV1.VERSION=1,UspV1.NAME="uspv1";