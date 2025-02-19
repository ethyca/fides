"use strict";Object.defineProperty(exports,"__esModule",{value:!0}),exports.UsTxGpcSegment=void 0;const CompressedBase64UrlEncoder_js_1=require("../base64/CompressedBase64UrlEncoder.js"),BitStringEncoder_js_1=require("../bitstring/BitStringEncoder.js"),EncodableBoolean_js_1=require("../datatype/EncodableBoolean.js"),EncodableFixedInteger_js_1=require("../datatype/EncodableFixedInteger.js"),DecodingError_js_1=require("../error/DecodingError.js"),EncodableBitStringFields_js_1=require("../field/EncodableBitStringFields.js"),UsTxField_js_1=require("../field/UsTxField.js"),UsTxField_js_2=require("../field/UsTxField.js"),AbstractLazilyEncodableSegment_js_1=require("./AbstractLazilyEncodableSegment.js");class UsTxGpcSegment extends AbstractLazilyEncodableSegment_js_1.AbstractLazilyEncodableSegment{constructor(e){super(),this.base64UrlEncoder=CompressedBase64UrlEncoder_js_1.CompressedBase64UrlEncoder.getInstance(),this.bitStringEncoder=BitStringEncoder_js_1.BitStringEncoder.getInstance(),e&&this.decode(e)}getFieldNames(){return UsTxField_js_1.USTX_GPC_SEGMENT_FIELD_NAMES}initializeFields(){let e=new EncodableBitStringFields_js_1.EncodableBitStringFields;return e.put(UsTxField_js_2.UsTxField.GPC_SEGMENT_TYPE.toString(),new EncodableFixedInteger_js_1.EncodableFixedInteger(2,1)),e.put(UsTxField_js_2.UsTxField.GPC_SEGMENT_INCLUDED.toString(),new EncodableBoolean_js_1.EncodableBoolean(!0)),e.put(UsTxField_js_2.UsTxField.GPC.toString(),new EncodableBoolean_js_1.EncodableBoolean(!1)),e}encodeSegment(e){let s=this.bitStringEncoder.encode(e,this.getFieldNames());return this.base64UrlEncoder.encode(s)}decodeSegment(e,s){null!=e&&0!==e.length||this.fields.reset(s);try{let t=this.base64UrlEncoder.decode(e);this.bitStringEncoder.decode(t,this.getFieldNames(),s)}catch(s){throw new DecodingError_js_1.DecodingError("Unable to decode UsTxGpcSegment '"+e+"'")}}}exports.UsTxGpcSegment=UsTxGpcSegment;