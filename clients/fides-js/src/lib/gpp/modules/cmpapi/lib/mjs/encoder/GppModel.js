import { HeaderV1 } from "./section/HeaderV1.js";
import { Sections } from "./section/Sections.js";
import { TcfCaV1 } from "./section/TcfCaV1.js";
import { TcfEuV2 } from "./section/TcfEuV2.js";
import { UspV1 } from "./section/UspV1.js";
import { UsNat } from "./section/UsNat.js";
import { UsCa } from "./section/UsCa.js";
import { UsVa } from "./section/UsVa.js";
import { UsCo } from "./section/UsCo.js";
import { UsUt } from "./section/UsUt.js";
import { UsCt } from "./section/UsCt.js";
import { UsFl } from "./section/UsFl.js";
import { UsMt } from "./section/UsMt.js";
import { UsOr } from "./section/UsOr.js";
import { UsTx } from "./section/UsTx.js";
import { InvalidFieldError } from "./error/InvalidFieldError.js";
import { DecodingError } from "./error/DecodingError.js";
import { HeaderV1Field } from "./field/HeaderV1Field.js";
import { UsDe } from "./section/UsDe.js";
import { UsIa } from "./section/UsIa.js";
import { UsNe } from "./section/UsNe.js";
import { UsNh } from "./section/UsNh.js";
import { UsNj } from "./section/UsNj.js";
import { UsTn } from "./section/UsTn.js";
export class GppModel {
    sections = new Map();
    encodedString = null;
    decoded = true;
    dirty = false;
    constructor(encodedString) {
        if (encodedString) {
            this.decode(encodedString);
        }
    }
    setFieldValue(sectionName, fieldName, value) {
        if (!this.decoded) {
            this.sections = this.decodeModel(this.encodedString);
            this.dirty = false;
            this.decoded = true;
        }
        let section = null;
        if (!this.sections.has(sectionName)) {
            if (sectionName === TcfCaV1.NAME) {
                section = new TcfCaV1();
                this.sections.set(TcfCaV1.NAME, section);
            }
            else if (sectionName === TcfEuV2.NAME) {
                section = new TcfEuV2();
                this.sections.set(TcfEuV2.NAME, section);
            }
            else if (sectionName === UspV1.NAME) {
                section = new UspV1();
                this.sections.set(UspV1.NAME, section);
            }
            else if (sectionName === UsNat.NAME) {
                section = new UsNat();
                this.sections.set(UsNat.NAME, section);
            }
            else if (sectionName === UsCa.NAME) {
                section = new UsCa();
                this.sections.set(UsCa.NAME, section);
            }
            else if (sectionName === UsVa.NAME) {
                section = new UsVa();
                this.sections.set(UsVa.NAME, section);
            }
            else if (sectionName === UsCo.NAME) {
                section = new UsCo();
                this.sections.set(UsCo.NAME, section);
            }
            else if (sectionName === UsUt.NAME) {
                section = new UsUt();
                this.sections.set(UsUt.NAME, section);
            }
            else if (sectionName === UsCt.NAME) {
                section = new UsCt();
                this.sections.set(UsCt.NAME, section);
            }
            else if (sectionName === UsFl.NAME) {
                section = new UsFl();
                this.sections.set(UsFl.NAME, section);
            }
            else if (sectionName === UsMt.NAME) {
                section = new UsMt();
                this.sections.set(UsMt.NAME, section);
            }
            else if (sectionName === UsOr.NAME) {
                section = new UsOr();
                this.sections.set(UsOr.NAME, section);
            }
            else if (sectionName === UsTx.NAME) {
                section = new UsTx();
                this.sections.set(UsTx.NAME, section);
            }
            else if (sectionName === UsDe.NAME) {
                section = new UsDe();
                this.sections.set(UsDe.NAME, section);
            }
            else if (sectionName === UsIa.NAME) {
                section = new UsIa();
                this.sections.set(UsIa.NAME, section);
            }
            else if (sectionName === UsNe.NAME) {
                section = new UsNe();
                this.sections.set(UsNe.NAME, section);
            }
            else if (sectionName === UsNh.NAME) {
                section = new UsNh();
                this.sections.set(UsNh.NAME, section);
            }
            else if (sectionName === UsNj.NAME) {
                section = new UsNj();
                this.sections.set(UsNj.NAME, section);
            }
            else if (sectionName === UsTn.NAME) {
                section = new UsTn();
                this.sections.set(UsTn.NAME, section);
            }
        }
        else {
            section = this.sections.get(sectionName);
        }
        if (section) {
            section.setFieldValue(fieldName, value);
            this.dirty = true;
            section.setIsDirty(true);
        }
        else {
            throw new InvalidFieldError(sectionName + "." + fieldName + " not found");
        }
    }
    setFieldValueBySectionId(sectionId, fieldName, value) {
        this.setFieldValue(Sections.SECTION_ID_NAME_MAP.get(sectionId), fieldName, value);
    }
    getFieldValue(sectionName, fieldName) {
        if (!this.decoded) {
            this.sections = this.decodeModel(this.encodedString);
            this.dirty = false;
            this.decoded = true;
        }
        if (this.sections.has(sectionName)) {
            return this.sections.get(sectionName).getFieldValue(fieldName);
        }
        else {
            return null;
        }
    }
    getFieldValueBySectionId(sectionId, fieldName) {
        return this.getFieldValue(Sections.SECTION_ID_NAME_MAP.get(sectionId), fieldName);
    }
    hasField(sectionName, fieldName) {
        if (!this.decoded) {
            this.sections = this.decodeModel(this.encodedString);
            this.dirty = false;
            this.decoded = true;
        }
        if (this.sections.has(sectionName)) {
            return this.sections.get(sectionName).hasField(fieldName);
        }
        else {
            return false;
        }
    }
    hasFieldBySectionId(sectionId, fieldName) {
        return this.hasField(Sections.SECTION_ID_NAME_MAP.get(sectionId), fieldName);
    }
    hasSection(sectionName) {
        if (!this.decoded) {
            this.sections = this.decodeModel(this.encodedString);
            this.dirty = false;
            this.decoded = true;
        }
        return this.sections.has(sectionName);
    }
    hasSectionId(sectionId) {
        return this.hasSection(Sections.SECTION_ID_NAME_MAP.get(sectionId));
    }
    deleteSection(sectionName) {
        // lazily decode
        if (!this.decoded && this.encodedString != null && this.encodedString.length > 0) {
            this.decode(this.encodedString);
        }
        this.sections.delete(sectionName);
        this.dirty = true;
    }
    deleteSectionById(sectionId) {
        this.deleteSection(Sections.SECTION_ID_NAME_MAP.get(sectionId));
    }
    clear() {
        this.sections.clear();
        this.encodedString = "DBAA";
        this.decoded = false;
        this.dirty = false;
    }
    getHeader() {
        if (!this.decoded) {
            this.sections = this.decodeModel(this.encodedString);
            this.dirty = false;
            this.decoded = true;
        }
        let header = new HeaderV1();
        header.setFieldValue("SectionIds", this.getSectionIds());
        return header.toObj();
    }
    getSection(sectionName) {
        if (!this.decoded) {
            this.sections = this.decodeModel(this.encodedString);
            this.dirty = false;
            this.decoded = true;
        }
        if (this.sections.has(sectionName)) {
            return this.sections.get(sectionName).toObj();
        }
        else {
            return null;
        }
    }
    getSectionIds() {
        if (!this.decoded) {
            this.sections = this.decodeModel(this.encodedString);
            this.dirty = false;
            this.decoded = true;
        }
        let sectionIds = [];
        for (let i = 0; i < Sections.SECTION_ORDER.length; i++) {
            let sectionName = Sections.SECTION_ORDER[i];
            if (this.sections.has(sectionName)) {
                let section = this.sections.get(sectionName);
                sectionIds.push(section.getId());
            }
        }
        return sectionIds;
    }
    encodeModel(sections) {
        let encodedSections = [];
        let sectionIds = [];
        for (let i = 0; i < Sections.SECTION_ORDER.length; i++) {
            let sectionName = Sections.SECTION_ORDER[i];
            if (sections.has(sectionName)) {
                let section = sections.get(sectionName);
                encodedSections.push(section.encode());
                sectionIds.push(section.getId());
            }
        }
        let header = new HeaderV1();
        header.setFieldValue("SectionIds", sectionIds);
        encodedSections.unshift(header.encode());
        return encodedSections.join("~");
    }
    decodeModel(str) {
        if (!str || str.length == 0 || str.startsWith("DB")) {
            let encodedSections = str.split("~");
            let sections = new Map();
            if (encodedSections[0].startsWith("D")) {
                //GPP String
                let header = new HeaderV1(encodedSections[0]);
                let sectionIds = header.getFieldValue("SectionIds");
                if (sectionIds.length !== encodedSections.length - 1) {
                    throw new DecodingError("Unable to decode '" +
                        str +
                        "'. The number of sections does not match the number of sections defined in the header.");
                }
                for (let i = 0; i < sectionIds.length; i++) {
                    let encodedSection = encodedSections[i + 1];
                    if (encodedSection.trim() === "") {
                        throw new DecodingError("Unable to decode '" + str + "'. Section " + (i + 1) + " is blank.");
                    }
                    if (sectionIds[i] === TcfCaV1.ID) {
                        let section = new TcfCaV1(encodedSections[i + 1]);
                        sections.set(TcfCaV1.NAME, section);
                    }
                    else if (sectionIds[i] === TcfEuV2.ID) {
                        let section = new TcfEuV2(encodedSections[i + 1]);
                        sections.set(TcfEuV2.NAME, section);
                    }
                    else if (sectionIds[i] === UspV1.ID) {
                        let section = new UspV1(encodedSections[i + 1]);
                        sections.set(UspV1.NAME, section);
                    }
                    else if (sectionIds[i] === UsNat.ID) {
                        let section = new UsNat(encodedSections[i + 1]);
                        sections.set(UsNat.NAME, section);
                    }
                    else if (sectionIds[i] === UsCa.ID) {
                        let section = new UsCa(encodedSections[i + 1]);
                        sections.set(UsCa.NAME, section);
                    }
                    else if (sectionIds[i] === UsVa.ID) {
                        let section = new UsVa(encodedSections[i + 1]);
                        sections.set(UsVa.NAME, section);
                    }
                    else if (sectionIds[i] === UsCo.ID) {
                        let section = new UsCo(encodedSections[i + 1]);
                        sections.set(UsCo.NAME, section);
                    }
                    else if (sectionIds[i] === UsUt.ID) {
                        let section = new UsUt(encodedSections[i + 1]);
                        sections.set(UsUt.NAME, section);
                    }
                    else if (sectionIds[i] === UsCt.ID) {
                        let section = new UsCt(encodedSections[i + 1]);
                        sections.set(UsCt.NAME, section);
                    }
                    else if (sectionIds[i] === UsFl.ID) {
                        let section = new UsFl(encodedSections[i + 1]);
                        sections.set(UsFl.NAME, section);
                    }
                    else if (sectionIds[i] === UsMt.ID) {
                        let section = new UsMt(encodedSections[i + 1]);
                        sections.set(UsMt.NAME, section);
                    }
                    else if (sectionIds[i] === UsOr.ID) {
                        let section = new UsOr(encodedSections[i + 1]);
                        sections.set(UsOr.NAME, section);
                    }
                    else if (sectionIds[i] === UsTx.ID) {
                        let section = new UsTx(encodedSections[i + 1]);
                        sections.set(UsTx.NAME, section);
                    }
                    else if (sectionIds[i] === UsDe.ID) {
                        let section = new UsDe(encodedSections[i + 1]);
                        sections.set(UsDe.NAME, section);
                    }
                    else if (sectionIds[i] === UsIa.ID) {
                        let section = new UsIa(encodedSections[i + 1]);
                        sections.set(UsIa.NAME, section);
                    }
                    else if (sectionIds[i] === UsNe.ID) {
                        let section = new UsNe(encodedSections[i + 1]);
                        sections.set(UsNe.NAME, section);
                    }
                    else if (sectionIds[i] === UsNh.ID) {
                        let section = new UsNh(encodedSections[i + 1]);
                        sections.set(UsNh.NAME, section);
                    }
                    else if (sectionIds[i] === UsNj.ID) {
                        let section = new UsNj(encodedSections[i + 1]);
                        sections.set(UsNj.NAME, section);
                    }
                    else if (sectionIds[i] === UsTn.ID) {
                        let section = new UsTn(encodedSections[i + 1]);
                        sections.set(UsTn.NAME, section);
                    }
                }
            }
            return sections;
        }
        else if (str.startsWith("C")) {
            // old tcfeu only string
            let sections = new Map();
            let section = new TcfEuV2(str);
            sections.set(TcfEuV2.NAME, section);
            let header = new HeaderV1();
            header.setFieldValue(HeaderV1Field.SECTION_IDS, [2]);
            sections.set(HeaderV1.NAME, section);
            return sections;
        }
        else {
            throw new DecodingError("Unable to decode '" + str + "'");
        }
    }
    encodeSection(sectionName) {
        if (!this.decoded) {
            this.sections = this.decodeModel(this.encodedString);
            this.dirty = false;
            this.decoded = true;
        }
        if (this.sections.has(sectionName)) {
            return this.sections.get(sectionName).encode();
        }
        else {
            return null;
        }
    }
    encodeSectionById(sectionId) {
        return this.encodeSection(Sections.SECTION_ID_NAME_MAP.get(sectionId));
    }
    decodeSection(sectionName, encodedString) {
        if (!this.decoded) {
            this.sections = this.decodeModel(this.encodedString);
            this.dirty = false;
            this.decoded = true;
        }
        let section = null;
        if (!this.sections.has(sectionName)) {
            if (sectionName === TcfCaV1.NAME) {
                section = new TcfCaV1();
                this.sections.set(TcfCaV1.NAME, section);
            }
            else if (sectionName === TcfEuV2.NAME) {
                section = new TcfEuV2();
                this.sections.set(TcfEuV2.NAME, section);
            }
            else if (sectionName === UspV1.NAME) {
                section = new UspV1();
                this.sections.set(UspV1.NAME, section);
            }
            else if (sectionName === UsNat.NAME) {
                section = new UsNat();
                this.sections.set(UsNat.NAME, section);
            }
            else if (sectionName === UsCa.NAME) {
                section = new UsCa();
                this.sections.set(UsCa.NAME, section);
            }
            else if (sectionName === UsVa.NAME) {
                section = new UsVa();
                this.sections.set(UsVa.NAME, section);
            }
            else if (sectionName === UsCo.NAME) {
                section = new UsCo();
                this.sections.set(UsCo.NAME, section);
            }
            else if (sectionName === UsUt.NAME) {
                section = new UsUt();
                this.sections.set(UsUt.NAME, section);
            }
            else if (sectionName === UsCt.NAME) {
                section = new UsCt();
                this.sections.set(UsCt.NAME, section);
            }
            else if (sectionName === UsFl.NAME) {
                section = new UsFl();
                this.sections.set(UsFl.NAME, section);
            }
            else if (sectionName === UsMt.NAME) {
                section = new UsMt();
                this.sections.set(UsMt.NAME, section);
            }
            else if (sectionName === UsOr.NAME) {
                section = new UsOr();
                this.sections.set(UsOr.NAME, section);
            }
            else if (sectionName === UsTx.NAME) {
                section = new UsTx();
                this.sections.set(UsTx.NAME, section);
            }
            else if (sectionName === UsDe.NAME) {
                section = new UsDe();
                this.sections.set(UsDe.NAME, section);
            }
            else if (sectionName === UsIa.NAME) {
                section = new UsIa();
                this.sections.set(UsIa.NAME, section);
            }
            else if (sectionName === UsNe.NAME) {
                section = new UsNe();
                this.sections.set(UsNe.NAME, section);
            }
            else if (sectionName === UsNh.NAME) {
                section = new UsNh();
                this.sections.set(UsNh.NAME, section);
            }
            else if (sectionName === UsNj.NAME) {
                section = new UsNj();
                this.sections.set(UsNj.NAME, section);
            }
            else if (sectionName === UsTn.NAME) {
                section = new UsTn();
                this.sections.set(UsTn.NAME, section);
            }
        }
        else {
            section = this.sections.get(sectionName);
        }
        if (section) {
            section.decode(encodedString);
            this.dirty = true;
        }
    }
    decodeSectionById(sectionId, encodedString) {
        this.decodeSection(Sections.SECTION_ID_NAME_MAP.get(sectionId), encodedString);
    }
    toObject() {
        if (!this.decoded) {
            this.sections = this.decodeModel(this.encodedString);
            this.dirty = false;
            this.decoded = true;
        }
        let obj = {};
        for (let i = 0; i < Sections.SECTION_ORDER.length; i++) {
            let sectionName = Sections.SECTION_ORDER[i];
            if (this.sections.has(sectionName)) {
                obj[sectionName] = this.sections.get(sectionName).toObj();
            }
        }
        return obj;
    }
    encode() {
        if (this.encodedString == null || this.encodedString.length === 0 || this.dirty) {
            this.encodedString = this.encodeModel(this.sections);
            this.dirty = false;
            this.decoded = true;
        }
        return this.encodedString;
    }
    decode(encodedString) {
        this.encodedString = encodedString;
        this.dirty = false;
        this.decoded = false;
    }
}
