"use strict";Object.defineProperty(exports,"__esModule",{value:!0}),exports.UsCo=void 0;const AbstractLazilyEncodableSection_js_1=require("./AbstractLazilyEncodableSection.js"),UsCoField_js_1=require("../field/UsCoField.js"),UsCoCoreSegment_js_1=require("../segment/UsCoCoreSegment.js"),UsCoGpcSegment_js_1=require("../segment/UsCoGpcSegment.js");class UsCo extends AbstractLazilyEncodableSection_js_1.AbstractLazilyEncodableSection{constructor(e){super(),e&&e.length>0&&this.decode(e)}getId(){return UsCo.ID}getName(){return UsCo.NAME}getVersion(){return UsCo.VERSION}initializeSegments(){let e=[];return e.push(new UsCoCoreSegment_js_1.UsCoCoreSegment),e.push(new UsCoGpcSegment_js_1.UsCoGpcSegment),e}decodeSection(e){let s=this.initializeSegments();if(null!=e&&0!==e.length){let t=e.split(".");t.length>0&&s[0].decode(t[0]),t.length>1?(s[1].setFieldValue(UsCoField_js_1.UsCoField.GPC_SEGMENT_INCLUDED,!0),s[1].decode(t[1])):s[1].setFieldValue(UsCoField_js_1.UsCoField.GPC_SEGMENT_INCLUDED,!1)}return s}encodeSection(e){let s=[];return e.length>=1&&(s.push(e[0].encode()),e.length>=2&&!0===e[1].getFieldValue(UsCoField_js_1.UsCoField.GPC_SEGMENT_INCLUDED)&&s.push(e[1].encode())),s.join(".")}}exports.UsCo=UsCo,UsCo.ID=10,UsCo.VERSION=1,UsCo.NAME="usco";