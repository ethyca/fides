"use strict";Object.defineProperty(exports,"__esModule",{value:!0}),exports.EncodableArrayOfFixedIntegerRanges=void 0;const DecodingError_js_1=require("../error/DecodingError.js"),EncodingError_js_1=require("../error/EncodingError.js"),StringUtil_js_1=require("../util/StringUtil.js"),AbstractEncodableBitStringDataType_js_1=require("./AbstractEncodableBitStringDataType.js"),EncodableFixedIntegerRange_js_1=require("./EncodableFixedIntegerRange.js"),RangeEntry_js_1=require("./RangeEntry.js"),SubstringError_js_1=require("./SubstringError.js"),FixedIntegerEncoder_js_1=require("./encoder/FixedIntegerEncoder.js"),FixedIntegerRangeEncoder_js_1=require("./encoder/FixedIntegerRangeEncoder.js");class EncodableArrayOfFixedIntegerRanges extends AbstractEncodableBitStringDataType_js_1.AbstractEncodableBitStringDataType{constructor(e,r,t,n=!0){super(n),this.keyBitStringLength=e,this.typeBitStringLength=r,this.setValue(t)}encode(){try{let e=this.value,r="";r+=FixedIntegerEncoder_js_1.FixedIntegerEncoder.encode(e.length,12);for(let t=0;t<e.length;t++){let n=e[t];r+=FixedIntegerEncoder_js_1.FixedIntegerEncoder.encode(n.getKey(),this.keyBitStringLength),r+=FixedIntegerEncoder_js_1.FixedIntegerEncoder.encode(n.getType(),this.typeBitStringLength),r+=FixedIntegerRangeEncoder_js_1.FixedIntegerRangeEncoder.encode(n.getIds())}return r}catch(e){throw new EncodingError_js_1.EncodingError(e)}}decode(e){try{let r=[],t=FixedIntegerEncoder_js_1.FixedIntegerEncoder.decode(StringUtil_js_1.StringUtil.substring(e,0,12)),n=12;for(let i=0;i<t;i++){let t=FixedIntegerEncoder_js_1.FixedIntegerEncoder.decode(StringUtil_js_1.StringUtil.substring(e,n,n+this.keyBitStringLength));n+=this.keyBitStringLength;let i=FixedIntegerEncoder_js_1.FixedIntegerEncoder.decode(StringUtil_js_1.StringUtil.substring(e,n,n+this.typeBitStringLength));n+=this.typeBitStringLength;let g=new EncodableFixedIntegerRange_js_1.EncodableFixedIntegerRange([]).substring(e,n),d=FixedIntegerRangeEncoder_js_1.FixedIntegerRangeEncoder.decode(g);n+=g.length,r.push(new RangeEntry_js_1.RangeEntry(t,i,d))}this.value=r}catch(e){throw new DecodingError_js_1.DecodingError(e)}}substring(e,r){try{let t="";t+=StringUtil_js_1.StringUtil.substring(e,r,r+12);let n=FixedIntegerEncoder_js_1.FixedIntegerEncoder.decode(t.toString()),i=r+t.length;for(let r=0;r<n;r++){let r=StringUtil_js_1.StringUtil.substring(e,i,i+this.keyBitStringLength);i+=r.length,t+=r;let n=StringUtil_js_1.StringUtil.substring(e,i,i+this.typeBitStringLength);i+=n.length,t+=n;let g=new EncodableFixedIntegerRange_js_1.EncodableFixedIntegerRange([]).substring(e,i);i+=g.length,t+=g}return t}catch(e){throw new SubstringError_js_1.SubstringError(e)}}}exports.EncodableArrayOfFixedIntegerRanges=EncodableArrayOfFixedIntegerRanges;