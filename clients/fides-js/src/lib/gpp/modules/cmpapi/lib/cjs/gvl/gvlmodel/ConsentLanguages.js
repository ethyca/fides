"use strict";Object.defineProperty(exports,"__esModule",{value:!0}),exports.ConsentLanguages=void 0;class ConsentLanguages{has(e){return ConsentLanguages.langSet.has(e)}forEach(e){ConsentLanguages.langSet.forEach(e)}get size(){return ConsentLanguages.langSet.size}}exports.ConsentLanguages=ConsentLanguages,ConsentLanguages.langSet=new Set(["BG","CA","CS","DA","DE","EL","EN","ES","ET","FI","FR","HR","HU","IT","JA","LT","LV","MT","NL","NO","PL","PT","RO","RU","SK","SL","SV","TR","ZH"]);