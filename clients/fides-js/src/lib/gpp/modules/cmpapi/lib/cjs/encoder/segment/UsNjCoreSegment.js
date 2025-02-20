"use strict";Object.defineProperty(exports,"__esModule",{value:!0}),exports.UsNjCoreSegment=void 0;const CompressedBase64UrlEncoder_js_1=require("../base64/CompressedBase64UrlEncoder.js"),BitStringEncoder_js_1=require("../bitstring/BitStringEncoder.js"),EncodableFixedInteger_js_1=require("../datatype/EncodableFixedInteger.js"),EncodableFixedIntegerList_js_1=require("../datatype/EncodableFixedIntegerList.js"),DecodingError_js_1=require("../error/DecodingError.js"),EncodableBitStringFields_js_1=require("../field/EncodableBitStringFields.js"),UsNjField_js_1=require("../field/UsNjField.js"),UsNjField_js_2=require("../field/UsNjField.js"),UsNj_js_1=require("../section/UsNj.js"),AbstractLazilyEncodableSegment_js_1=require("./AbstractLazilyEncodableSegment.js");class UsNjCoreSegment extends AbstractLazilyEncodableSegment_js_1.AbstractLazilyEncodableSegment{constructor(e){super(),this.base64UrlEncoder=CompressedBase64UrlEncoder_js_1.CompressedBase64UrlEncoder.getInstance(),this.bitStringEncoder=BitStringEncoder_js_1.BitStringEncoder.getInstance(),e&&this.decode(e)}getFieldNames(){return UsNjField_js_1.USNJ_CORE_SEGMENT_FIELD_NAMES}initializeFields(){const e=new class{test(e){return e>=0&&e<=2}},t=new class{test(e){return e>=1&&e<=2}},i=new class{test(e){for(let t=0;t<e.length;t++){let i=e[t];if(i<0||i>2)return!1}return!0}};let s=new EncodableBitStringFields_js_1.EncodableBitStringFields;return s.put(UsNjField_js_2.UsNjField.VERSION.toString(),new EncodableFixedInteger_js_1.EncodableFixedInteger(6,UsNj_js_1.UsNj.VERSION)),s.put(UsNjField_js_2.UsNjField.PROCESSING_NOTICE.toString(),new EncodableFixedInteger_js_1.EncodableFixedInteger(2,0).withValidator(e)),s.put(UsNjField_js_2.UsNjField.SALE_OPT_OUT_NOTICE.toString(),new EncodableFixedInteger_js_1.EncodableFixedInteger(2,0).withValidator(e)),s.put(UsNjField_js_2.UsNjField.TARGETED_ADVERTISING_OPT_OUT_NOTICE.toString(),new EncodableFixedInteger_js_1.EncodableFixedInteger(2,0).withValidator(e)),s.put(UsNjField_js_2.UsNjField.SALE_OPT_OUT.toString(),new EncodableFixedInteger_js_1.EncodableFixedInteger(2,0).withValidator(e)),s.put(UsNjField_js_2.UsNjField.TARGETED_ADVERTISING_OPT_OUT.toString(),new EncodableFixedInteger_js_1.EncodableFixedInteger(2,0).withValidator(e)),s.put(UsNjField_js_2.UsNjField.SENSITIVE_DATA_PROCESSING.toString(),new EncodableFixedIntegerList_js_1.EncodableFixedIntegerList(2,[0,0,0,0,0,0,0,0,0,0]).withValidator(i)),s.put(UsNjField_js_2.UsNjField.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS.toString(),new EncodableFixedIntegerList_js_1.EncodableFixedIntegerList(2,[0,0,0,0,0]).withValidator(i)),s.put(UsNjField_js_2.UsNjField.ADDITIONAL_DATA_PROCESSING_CONSENT.toString(),new EncodableFixedInteger_js_1.EncodableFixedInteger(2,0).withValidator(e)),s.put(UsNjField_js_2.UsNjField.MSPA_COVERED_TRANSACTION.toString(),new EncodableFixedInteger_js_1.EncodableFixedInteger(2,1).withValidator(t)),s.put(UsNjField_js_2.UsNjField.MSPA_OPT_OUT_OPTION_MODE.toString(),new EncodableFixedInteger_js_1.EncodableFixedInteger(2,0).withValidator(e)),s.put(UsNjField_js_2.UsNjField.MSPA_SERVICE_PROVIDER_MODE.toString(),new EncodableFixedInteger_js_1.EncodableFixedInteger(2,0).withValidator(e)),s}encodeSegment(e){let t=this.bitStringEncoder.encode(e,this.getFieldNames());return this.base64UrlEncoder.encode(t)}decodeSegment(e,t){null!=e&&0!==e.length||this.fields.reset(t);try{let i=this.base64UrlEncoder.decode(e);this.bitStringEncoder.decode(i,this.getFieldNames(),t)}catch(t){throw new DecodingError_js_1.DecodingError("Unable to decode UsNjCoreSegment '"+e+"'")}}}exports.UsNjCoreSegment=UsNjCoreSegment;