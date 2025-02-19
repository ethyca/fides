"use strict";Object.defineProperty(exports,"__esModule",{value:!0}),exports.FixedBitfieldEncoder=void 0;const DecodingError_js_1=require("../../error/DecodingError.js"),EncodingError_js_1=require("../../error/EncodingError.js"),BooleanEncoder_js_1=require("./BooleanEncoder.js");class FixedBitfieldEncoder{static encode(e,r){if(e.length>r)throw new EncodingError_js_1.EncodingError("Too many values '"+e.length+"'");let o="";for(let r=0;r<e.length;r++)o+=BooleanEncoder_js_1.BooleanEncoder.encode(e[r]);for(;o.length<r;)o+="0";return o}static decode(e){if(!/^[0-1]*$/.test(e))throw new DecodingError_js_1.DecodingError("Undecodable FixedBitfield '"+e+"'");let r=[];for(let o=0;o<e.length;o++)r.push(BooleanEncoder_js_1.BooleanEncoder.decode(e.substring(o,o+1)));return r}}exports.FixedBitfieldEncoder=FixedBitfieldEncoder;