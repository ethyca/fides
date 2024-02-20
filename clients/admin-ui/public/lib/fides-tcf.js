(function (y, M) {
  typeof exports == "object" && typeof module < "u"
    ? M(exports)
    : typeof define == "function" && define.amd
    ? define(["exports"], M)
    : ((y = typeof globalThis < "u" ? globalThis : y || self),
      M((y.Fides = {})));
})(this, function (y) {
  "use strict";
  class M extends Error {
    constructor(e) {
      super(e), (this.name = "DecodingError");
    }
  }
  class Z extends Error {
    constructor(e) {
      super(e), (this.name = "EncodingError");
    }
  }
  class Se extends Error {
    constructor(e) {
      super(e), (this.name = "GVLError");
    }
  }
  class X extends Error {
    constructor(e, n, i = "") {
      super(`invalid value ${n} passed for ${e} ${i}`),
        (this.name = "TCModelError");
    }
  }
  class ct {
    static DICT =
      "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";
    static REVERSE_DICT = new Map([
      ["A", 0],
      ["B", 1],
      ["C", 2],
      ["D", 3],
      ["E", 4],
      ["F", 5],
      ["G", 6],
      ["H", 7],
      ["I", 8],
      ["J", 9],
      ["K", 10],
      ["L", 11],
      ["M", 12],
      ["N", 13],
      ["O", 14],
      ["P", 15],
      ["Q", 16],
      ["R", 17],
      ["S", 18],
      ["T", 19],
      ["U", 20],
      ["V", 21],
      ["W", 22],
      ["X", 23],
      ["Y", 24],
      ["Z", 25],
      ["a", 26],
      ["b", 27],
      ["c", 28],
      ["d", 29],
      ["e", 30],
      ["f", 31],
      ["g", 32],
      ["h", 33],
      ["i", 34],
      ["j", 35],
      ["k", 36],
      ["l", 37],
      ["m", 38],
      ["n", 39],
      ["o", 40],
      ["p", 41],
      ["q", 42],
      ["r", 43],
      ["s", 44],
      ["t", 45],
      ["u", 46],
      ["v", 47],
      ["w", 48],
      ["x", 49],
      ["y", 50],
      ["z", 51],
      ["0", 52],
      ["1", 53],
      ["2", 54],
      ["3", 55],
      ["4", 56],
      ["5", 57],
      ["6", 58],
      ["7", 59],
      ["8", 60],
      ["9", 61],
      ["-", 62],
      ["_", 63],
    ]);
    static BASIS = 6;
    static LCM = 24;
    static encode(e) {
      if (!/^[0-1]+$/.test(e)) throw new Z("Invalid bitField");
      const n = e.length % this.LCM;
      e += n ? "0".repeat(this.LCM - n) : "";
      let i = "";
      for (let s = 0; s < e.length; s += this.BASIS)
        i += this.DICT[parseInt(e.substr(s, this.BASIS), 2)];
      return i;
    }
    static decode(e) {
      if (!/^[A-Za-z0-9\-_]+$/.test(e))
        throw new M("Invalidly encoded Base64URL string");
      let n = "";
      for (let i = 0; i < e.length; i++) {
        const s = this.REVERSE_DICT.get(e[i]).toString(2);
        n += "0".repeat(this.BASIS - s.length) + s;
      }
      return n;
    }
  }
  class ee {
    static langSet = new Set([
      "AR",
      "BG",
      "BS",
      "CA",
      "CS",
      "DA",
      "DE",
      "EL",
      "EN",
      "ES",
      "ET",
      "EU",
      "FI",
      "FR",
      "GL",
      "HR",
      "HU",
      "IT",
      "JA",
      "LT",
      "LV",
      "MT",
      "NL",
      "NO",
      "PL",
      "PT-BR",
      "PT-PT",
      "RO",
      "RU",
      "SK",
      "SL",
      "SR-LATN",
      "SR-CYRL",
      "SV",
      "TR",
      "ZH",
    ]);
    has(e) {
      return ee.langSet.has(e);
    }
    parseLanguage(e) {
      e = e.toUpperCase();
      const n = e.split("-")[0];
      if (e.length >= 2 && n.length == 2) {
        if (ee.langSet.has(e)) return e;
        if (ee.langSet.has(n)) return n;
        const i = n + "-" + n;
        if (ee.langSet.has(i)) return i;
        for (const s of ee.langSet)
          if (s.indexOf(e) !== -1 || s.indexOf(n) !== -1) return s;
      }
      throw new Error(`unsupported language ${e}`);
    }
    forEach(e) {
      ee.langSet.forEach(e);
    }
    get size() {
      return ee.langSet.size;
    }
  }
  class v {
    static cmpId = "cmpId";
    static cmpVersion = "cmpVersion";
    static consentLanguage = "consentLanguage";
    static consentScreen = "consentScreen";
    static created = "created";
    static supportOOB = "supportOOB";
    static isServiceSpecific = "isServiceSpecific";
    static lastUpdated = "lastUpdated";
    static numCustomPurposes = "numCustomPurposes";
    static policyVersion = "policyVersion";
    static publisherCountryCode = "publisherCountryCode";
    static publisherCustomConsents = "publisherCustomConsents";
    static publisherCustomLegitimateInterests =
      "publisherCustomLegitimateInterests";
    static publisherLegitimateInterests = "publisherLegitimateInterests";
    static publisherConsents = "publisherConsents";
    static publisherRestrictions = "publisherRestrictions";
    static purposeConsents = "purposeConsents";
    static purposeLegitimateInterests = "purposeLegitimateInterests";
    static purposeOneTreatment = "purposeOneTreatment";
    static specialFeatureOptins = "specialFeatureOptins";
    static useNonStandardTexts = "useNonStandardTexts";
    static vendorConsents = "vendorConsents";
    static vendorLegitimateInterests = "vendorLegitimateInterests";
    static vendorListVersion = "vendorListVersion";
    static vendorsAllowed = "vendorsAllowed";
    static vendorsDisclosed = "vendorsDisclosed";
    static version = "version";
  }
  class Pe {
    clone() {
      const e = new this.constructor();
      return (
        Object.keys(this).forEach((i) => {
          const s = this.deepClone(this[i]);
          s !== void 0 && (e[i] = s);
        }),
        e
      );
    }
    deepClone(e) {
      const n = typeof e;
      if (n === "number" || n === "string" || n === "boolean") return e;
      if (e !== null && n === "object") {
        if (typeof e.clone == "function") return e.clone();
        if (e instanceof Date) return new Date(e.getTime());
        if (e[Symbol.iterator] !== void 0) {
          const i = [];
          for (const s of e) i.push(this.deepClone(s));
          return e instanceof Array ? i : new e.constructor(i);
        } else {
          const i = {};
          for (const s in e)
            e.hasOwnProperty(s) && (i[s] = this.deepClone(e[s]));
          return i;
        }
      }
    }
  }
  var q;
  (function (t) {
    (t[(t.NOT_ALLOWED = 0)] = "NOT_ALLOWED"),
      (t[(t.REQUIRE_CONSENT = 1)] = "REQUIRE_CONSENT"),
      (t[(t.REQUIRE_LI = 2)] = "REQUIRE_LI");
  })(q || (q = {}));
  class oe extends Pe {
    static hashSeparator = "-";
    purposeId_;
    restrictionType;
    constructor(e, n) {
      super(),
        e !== void 0 && (this.purposeId = e),
        n !== void 0 && (this.restrictionType = n);
    }
    static unHash(e) {
      const n = e.split(this.hashSeparator),
        i = new oe();
      if (n.length !== 2) throw new X("hash", e);
      return (
        (i.purposeId = parseInt(n[0], 10)),
        (i.restrictionType = parseInt(n[1], 10)),
        i
      );
    }
    get hash() {
      if (!this.isValid())
        throw new Error("cannot hash invalid PurposeRestriction");
      return `${this.purposeId}${oe.hashSeparator}${this.restrictionType}`;
    }
    get purposeId() {
      return this.purposeId_;
    }
    set purposeId(e) {
      this.purposeId_ = e;
    }
    isValid() {
      return (
        Number.isInteger(this.purposeId) &&
        this.purposeId > 0 &&
        (this.restrictionType === q.NOT_ALLOWED ||
          this.restrictionType === q.REQUIRE_CONSENT ||
          this.restrictionType === q.REQUIRE_LI)
      );
    }
    isSameAs(e) {
      return (
        this.purposeId === e.purposeId &&
        this.restrictionType === e.restrictionType
      );
    }
  }
  class Gt extends Pe {
    bitLength = 0;
    map = new Map();
    gvl_;
    has(e) {
      return this.map.has(e);
    }
    isOkToHave(e, n, i) {
      let s = !0;
      if (this.gvl?.vendors) {
        const o = this.gvl.vendors[i];
        if (o)
          if (e === q.NOT_ALLOWED)
            s = o.legIntPurposes.includes(n) || o.purposes.includes(n);
          else if (o.flexiblePurposes.length)
            switch (e) {
              case q.REQUIRE_CONSENT:
                s =
                  o.flexiblePurposes.includes(n) &&
                  o.legIntPurposes.includes(n);
                break;
              case q.REQUIRE_LI:
                s = o.flexiblePurposes.includes(n) && o.purposes.includes(n);
                break;
            }
          else s = !1;
        else s = !1;
      }
      return s;
    }
    add(e, n) {
      if (this.isOkToHave(n.restrictionType, n.purposeId, e)) {
        const i = n.hash;
        this.has(i) || (this.map.set(i, new Set()), (this.bitLength = 0)),
          this.map.get(i).add(e);
      }
    }
    restrictPurposeToLegalBasis(e) {
      const n = Array.from(this.gvl.vendorIds),
        i = e.hash,
        s = n[n.length - 1],
        o = [...Array(s).keys()].map((d) => d + 1);
      if (!this.has(i)) this.map.set(i, new Set(o)), (this.bitLength = 0);
      else for (let d = 1; d <= s; d++) this.map.get(i).add(d);
    }
    getVendors(e) {
      let n = [];
      if (e) {
        const i = e.hash;
        this.has(i) && (n = Array.from(this.map.get(i)));
      } else {
        const i = new Set();
        this.map.forEach((s) => {
          s.forEach((o) => {
            i.add(o);
          });
        }),
          (n = Array.from(i));
      }
      return n.sort((i, s) => i - s);
    }
    getRestrictionType(e, n) {
      let i;
      return (
        this.getRestrictions(e).forEach((s) => {
          s.purposeId === n &&
            (i === void 0 || i > s.restrictionType) &&
            (i = s.restrictionType);
        }),
        i
      );
    }
    vendorHasRestriction(e, n) {
      let i = !1;
      const s = this.getRestrictions(e);
      for (let o = 0; o < s.length && !i; o++) i = n.isSameAs(s[o]);
      return i;
    }
    getMaxVendorId() {
      let e = 0;
      return (
        this.map.forEach((n) => {
          e = Math.max(Array.from(n)[n.size - 1], e);
        }),
        e
      );
    }
    getRestrictions(e) {
      const n = [];
      return (
        this.map.forEach((i, s) => {
          e ? i.has(e) && n.push(oe.unHash(s)) : n.push(oe.unHash(s));
        }),
        n
      );
    }
    getPurposes() {
      const e = new Set();
      return (
        this.map.forEach((n, i) => {
          e.add(oe.unHash(i).purposeId);
        }),
        Array.from(e)
      );
    }
    remove(e, n) {
      const i = n.hash,
        s = this.map.get(i);
      s &&
        (s.delete(e),
        s.size == 0 && (this.map.delete(i), (this.bitLength = 0)));
    }
    set gvl(e) {
      this.gvl_ ||
        ((this.gvl_ = e),
        this.map.forEach((n, i) => {
          const s = oe.unHash(i);
          Array.from(n).forEach((d) => {
            this.isOkToHave(s.restrictionType, s.purposeId, d) || n.delete(d);
          });
        }));
    }
    get gvl() {
      return this.gvl_;
    }
    isEmpty() {
      return this.map.size === 0;
    }
    get numRestrictions() {
      return this.map.size;
    }
  }
  var Kt;
  (function (t) {
    (t.COOKIE = "cookie"), (t.WEB = "web"), (t.APP = "app");
  })(Kt || (Kt = {}));
  var P;
  (function (t) {
    (t.CORE = "core"),
      (t.VENDORS_DISCLOSED = "vendorsDisclosed"),
      (t.VENDORS_ALLOWED = "vendorsAllowed"),
      (t.PUBLISHER_TC = "publisherTC");
  })(P || (P = {}));
  class Yt {
    static ID_TO_KEY = [
      P.CORE,
      P.VENDORS_DISCLOSED,
      P.VENDORS_ALLOWED,
      P.PUBLISHER_TC,
    ];
    static KEY_TO_ID = {
      [P.CORE]: 0,
      [P.VENDORS_DISCLOSED]: 1,
      [P.VENDORS_ALLOWED]: 2,
      [P.PUBLISHER_TC]: 3,
    };
  }
  class D extends Pe {
    bitLength = 0;
    maxId_ = 0;
    set_ = new Set();
    *[Symbol.iterator]() {
      for (let e = 1; e <= this.maxId; e++) yield [e, this.has(e)];
    }
    values() {
      return this.set_.values();
    }
    get maxId() {
      return this.maxId_;
    }
    has(e) {
      return this.set_.has(e);
    }
    unset(e) {
      Array.isArray(e)
        ? e.forEach((n) => this.unset(n))
        : typeof e == "object"
        ? this.unset(Object.keys(e).map((n) => Number(n)))
        : (this.set_.delete(Number(e)),
          (this.bitLength = 0),
          e === this.maxId &&
            ((this.maxId_ = 0),
            this.set_.forEach((n) => {
              this.maxId_ = Math.max(this.maxId, n);
            })));
    }
    isIntMap(e) {
      let n = typeof e == "object";
      return (
        (n =
          n &&
          Object.keys(e).every((i) => {
            let s = Number.isInteger(parseInt(i, 10));
            return (
              (s = s && this.isValidNumber(e[i].id)),
              (s = s && e[i].name !== void 0),
              s
            );
          })),
        n
      );
    }
    isValidNumber(e) {
      return parseInt(e, 10) > 0;
    }
    isSet(e) {
      let n = !1;
      return (
        e instanceof Set && (n = Array.from(e).every(this.isValidNumber)), n
      );
    }
    set(e) {
      if (Array.isArray(e)) e.forEach((n) => this.set(n));
      else if (this.isSet(e)) this.set(Array.from(e));
      else if (this.isIntMap(e)) this.set(Object.keys(e).map((n) => Number(n)));
      else if (this.isValidNumber(e))
        this.set_.add(e),
          (this.maxId_ = Math.max(this.maxId, e)),
          (this.bitLength = 0);
      else
        throw new X(
          "set()",
          e,
          "must be positive integer array, positive integer, Set<number>, or IntMap"
        );
    }
    empty() {
      this.set_ = new Set();
    }
    forEach(e) {
      for (let n = 1; n <= this.maxId; n++) e(this.has(n), n);
    }
    get size() {
      return this.set_.size;
    }
    setAll(e) {
      this.set(e);
    }
  }
  class _ {
    static [v.cmpId] = 12;
    static [v.cmpVersion] = 12;
    static [v.consentLanguage] = 12;
    static [v.consentScreen] = 6;
    static [v.created] = 36;
    static [v.isServiceSpecific] = 1;
    static [v.lastUpdated] = 36;
    static [v.policyVersion] = 6;
    static [v.publisherCountryCode] = 12;
    static [v.publisherLegitimateInterests] = 24;
    static [v.publisherConsents] = 24;
    static [v.purposeConsents] = 24;
    static [v.purposeLegitimateInterests] = 24;
    static [v.purposeOneTreatment] = 1;
    static [v.specialFeatureOptins] = 12;
    static [v.useNonStandardTexts] = 1;
    static [v.vendorListVersion] = 12;
    static [v.version] = 6;
    static anyBoolean = 1;
    static encodingType = 1;
    static maxId = 16;
    static numCustomPurposes = 6;
    static numEntries = 12;
    static numRestrictions = 12;
    static purposeId = 6;
    static restrictionType = 2;
    static segmentType = 3;
    static singleOrRange = 1;
    static vendorId = 16;
  }
  class W {
    static encode(e) {
      return String(Number(e));
    }
    static decode(e) {
      return e === "1";
    }
  }
  class I {
    static encode(e, n) {
      let i;
      if (
        (typeof e == "string" && (e = parseInt(e, 10)),
        (i = e.toString(2)),
        i.length > n || e < 0)
      )
        throw new Z(`${e} too large to encode into ${n}`);
      return i.length < n && (i = "0".repeat(n - i.length) + i), i;
    }
    static decode(e, n) {
      if (n !== e.length) throw new M("invalid bit length");
      return parseInt(e, 2);
    }
  }
  class qt {
    static encode(e, n) {
      return I.encode(Math.round(e.getTime() / 100), n);
    }
    static decode(e, n) {
      if (n !== e.length) throw new M("invalid bit length");
      const i = new Date();
      return i.setTime(I.decode(e, n) * 100), i;
    }
  }
  class re {
    static encode(e, n) {
      let i = "";
      for (let s = 1; s <= n; s++) i += W.encode(e.has(s));
      return i;
    }
    static decode(e, n) {
      if (e.length !== n) throw new M("bitfield encoding length mismatch");
      const i = new D();
      for (let s = 1; s <= n; s++) W.decode(e[s - 1]) && i.set(s);
      return (i.bitLength = e.length), i;
    }
  }
  class Wt {
    static encode(e, n) {
      e = e.toUpperCase();
      const i = 65,
        s = e.charCodeAt(0) - i,
        o = e.charCodeAt(1) - i;
      if (s < 0 || s > 25 || o < 0 || o > 25)
        throw new Z(`invalid language code: ${e}`);
      if (n % 2 === 1) throw new Z(`numBits must be even, ${n} is not valid`);
      n = n / 2;
      const d = I.encode(s, n),
        a = I.encode(o, n);
      return d + a;
    }
    static decode(e, n) {
      let i;
      if (n === e.length && !(e.length % 2)) {
        const o = e.length / 2,
          d = I.decode(e.slice(0, o), o) + 65,
          a = I.decode(e.slice(o), o) + 65;
        i = String.fromCharCode(d) + String.fromCharCode(a);
      } else throw new M("invalid bit length for language");
      return i;
    }
  }
  class qs {
    static encode(e) {
      let n = I.encode(e.numRestrictions, _.numRestrictions);
      if (!e.isEmpty()) {
        const i = (s, o) => {
          for (let d = s + 1; d <= o; d++) if (e.gvl.vendorIds.has(d)) return d;
          return s;
        };
        e.getRestrictions().forEach((s) => {
          (n += I.encode(s.purposeId, _.purposeId)),
            (n += I.encode(s.restrictionType, _.restrictionType));
          const o = e.getVendors(s),
            d = o.length;
          let a = 0,
            r = 0,
            p = "";
          for (let l = 0; l < d; l++) {
            const f = o[l];
            if (
              (r === 0 && (a++, (r = f)),
              l === d - 1 || o[l + 1] > i(f, o[d - 1]))
            ) {
              const u = f !== r;
              (p += W.encode(u)),
                (p += I.encode(r, _.vendorId)),
                u && (p += I.encode(f, _.vendorId)),
                (r = 0);
            }
          }
          (n += I.encode(a, _.numEntries)), (n += p);
        });
      }
      return n;
    }
    static decode(e) {
      let n = 0;
      const i = new Gt(),
        s = I.decode(e.substr(n, _.numRestrictions), _.numRestrictions);
      n += _.numRestrictions;
      for (let o = 0; o < s; o++) {
        const d = I.decode(e.substr(n, _.purposeId), _.purposeId);
        n += _.purposeId;
        const a = I.decode(e.substr(n, _.restrictionType), _.restrictionType);
        n += _.restrictionType;
        const r = new oe(d, a),
          p = I.decode(e.substr(n, _.numEntries), _.numEntries);
        n += _.numEntries;
        for (let l = 0; l < p; l++) {
          const f = W.decode(e.substr(n, _.anyBoolean));
          n += _.anyBoolean;
          const u = I.decode(e.substr(n, _.vendorId), _.vendorId);
          if (((n += _.vendorId), f)) {
            const g = I.decode(e.substr(n, _.vendorId), _.vendorId);
            if (((n += _.vendorId), g < u))
              throw new M(
                `Invalid RangeEntry: endVendorId ${g} is less than ${u}`
              );
            for (let h = u; h <= g; h++) i.add(h, r);
          } else i.add(u, r);
        }
      }
      return (i.bitLength = n), i;
    }
  }
  var Te;
  (function (t) {
    (t[(t.FIELD = 0)] = "FIELD"), (t[(t.RANGE = 1)] = "RANGE");
  })(Te || (Te = {}));
  class ke {
    static encode(e) {
      const n = [];
      let i = [],
        s = I.encode(e.maxId, _.maxId),
        o = "",
        d;
      const a = _.maxId + _.encodingType,
        r = a + e.maxId,
        p = _.vendorId * 2 + _.singleOrRange + _.numEntries;
      let l = a + _.numEntries;
      return (
        e.forEach((f, u) => {
          (o += W.encode(f)),
            (d = e.maxId > p && l < r),
            d &&
              f &&
              (e.has(u + 1)
                ? i.length === 0 &&
                  (i.push(u), (l += _.singleOrRange), (l += _.vendorId))
                : (i.push(u), (l += _.vendorId), n.push(i), (i = [])));
        }),
        d
          ? ((s += String(Te.RANGE)), (s += this.buildRangeEncoding(n)))
          : ((s += String(Te.FIELD)), (s += o)),
        s
      );
    }
    static decode(e, n) {
      let i,
        s = 0;
      const o = I.decode(e.substr(s, _.maxId), _.maxId);
      s += _.maxId;
      const d = I.decode(e.charAt(s), _.encodingType);
      if (((s += _.encodingType), d === Te.RANGE)) {
        if (((i = new D()), n === 1)) {
          if (e.substr(s, 1) === "1")
            throw new M("Unable to decode default consent=1");
          s++;
        }
        const a = I.decode(e.substr(s, _.numEntries), _.numEntries);
        s += _.numEntries;
        for (let r = 0; r < a; r++) {
          const p = W.decode(e.charAt(s));
          s += _.singleOrRange;
          const l = I.decode(e.substr(s, _.vendorId), _.vendorId);
          if (((s += _.vendorId), p)) {
            const f = I.decode(e.substr(s, _.vendorId), _.vendorId);
            s += _.vendorId;
            for (let u = l; u <= f; u++) i.set(u);
          } else i.set(l);
        }
      } else {
        const a = e.substr(s, o);
        (s += o), (i = re.decode(a, o));
      }
      return (i.bitLength = s), i;
    }
    static buildRangeEncoding(e) {
      const n = e.length;
      let i = I.encode(n, _.numEntries);
      return (
        e.forEach((s) => {
          const o = s.length === 1;
          (i += W.encode(!o)),
            (i += I.encode(s[0], _.vendorId)),
            o || (i += I.encode(s[1], _.vendorId));
        }),
        i
      );
    }
  }
  function Qt() {
    return {
      [v.version]: I,
      [v.created]: qt,
      [v.lastUpdated]: qt,
      [v.cmpId]: I,
      [v.cmpVersion]: I,
      [v.consentScreen]: I,
      [v.consentLanguage]: Wt,
      [v.vendorListVersion]: I,
      [v.policyVersion]: I,
      [v.isServiceSpecific]: W,
      [v.useNonStandardTexts]: W,
      [v.specialFeatureOptins]: re,
      [v.purposeConsents]: re,
      [v.purposeLegitimateInterests]: re,
      [v.purposeOneTreatment]: W,
      [v.publisherCountryCode]: Wt,
      [v.vendorConsents]: ke,
      [v.vendorLegitimateInterests]: ke,
      [v.publisherRestrictions]: qs,
      segmentType: I,
      [v.vendorsDisclosed]: ke,
      [v.vendorsAllowed]: ke,
      [v.publisherConsents]: re,
      [v.publisherLegitimateInterests]: re,
      [v.numCustomPurposes]: I,
      [v.publisherCustomConsents]: re,
      [v.publisherCustomLegitimateInterests]: re,
    };
  }
  class Ws {
    1 = {
      [P.CORE]: [
        v.version,
        v.created,
        v.lastUpdated,
        v.cmpId,
        v.cmpVersion,
        v.consentScreen,
        v.consentLanguage,
        v.vendorListVersion,
        v.purposeConsents,
        v.vendorConsents,
      ],
    };
    2 = {
      [P.CORE]: [
        v.version,
        v.created,
        v.lastUpdated,
        v.cmpId,
        v.cmpVersion,
        v.consentScreen,
        v.consentLanguage,
        v.vendorListVersion,
        v.policyVersion,
        v.isServiceSpecific,
        v.useNonStandardTexts,
        v.specialFeatureOptins,
        v.purposeConsents,
        v.purposeLegitimateInterests,
        v.purposeOneTreatment,
        v.publisherCountryCode,
        v.vendorConsents,
        v.vendorLegitimateInterests,
        v.publisherRestrictions,
      ],
      [P.PUBLISHER_TC]: [
        v.publisherConsents,
        v.publisherLegitimateInterests,
        v.numCustomPurposes,
        v.publisherCustomConsents,
        v.publisherCustomLegitimateInterests,
      ],
      [P.VENDORS_ALLOWED]: [v.vendorsAllowed],
      [P.VENDORS_DISCLOSED]: [v.vendorsDisclosed],
    };
  }
  class Qs {
    1 = [P.CORE];
    2 = [P.CORE];
    constructor(e, n) {
      if (e.version === 2)
        if (e.isServiceSpecific) this[2].push(P.PUBLISHER_TC);
        else {
          const i = !!(n && n.isForVendors);
          (!i || e[v.supportOOB] === !0) && this[2].push(P.VENDORS_DISCLOSED),
            i &&
              (e[v.supportOOB] &&
                e[v.vendorsAllowed].size > 0 &&
                this[2].push(P.VENDORS_ALLOWED),
              this[2].push(P.PUBLISHER_TC));
        }
    }
  }
  class Jt {
    static fieldSequence = new Ws();
    static encode(e, n) {
      let i;
      try {
        i = this.fieldSequence[String(e.version)][n];
      } catch {
        throw new Z(`Unable to encode version: ${e.version}, segment: ${n}`);
      }
      let s = "";
      n !== P.CORE && (s = I.encode(Yt.KEY_TO_ID[n], _.segmentType));
      const o = Qt();
      return (
        i.forEach((d) => {
          const a = e[d],
            r = o[d];
          let p = _[d];
          p === void 0 &&
            this.isPublisherCustom(d) &&
            (p = Number(e[v.numCustomPurposes]));
          try {
            s += r.encode(a, p);
          } catch (l) {
            throw new Z(`Error encoding ${n}->${d}: ${l.message}`);
          }
        }),
        ct.encode(s)
      );
    }
    static decode(e, n, i) {
      const s = ct.decode(e);
      let o = 0;
      i === P.CORE &&
        (n.version = I.decode(s.substr(o, _[v.version]), _[v.version])),
        i !== P.CORE && (o += _.segmentType);
      const d = this.fieldSequence[String(n.version)][i],
        a = Qt();
      return (
        d.forEach((r) => {
          const p = a[r];
          let l = _[r];
          if (
            (l === void 0 &&
              this.isPublisherCustom(r) &&
              (l = Number(n[v.numCustomPurposes])),
            l !== 0)
          ) {
            const f = s.substr(o, l);
            if (
              (p === ke
                ? (n[r] = p.decode(f, n.version))
                : (n[r] = p.decode(f, l)),
              Number.isInteger(l))
            )
              o += l;
            else if (Number.isInteger(n[r].bitLength)) o += n[r].bitLength;
            else throw new M(r);
          }
        }),
        n
      );
    }
    static isPublisherCustom(e) {
      return e.indexOf("publisherCustom") === 0;
    }
  }
  class Js {
    static processor = [
      (e) => e,
      (e, n) => {
        (e.publisherRestrictions.gvl = n),
          e.purposeLegitimateInterests.unset([1, 3, 4, 5, 6]);
        const i = new Map();
        return (
          i.set("legIntPurposes", e.vendorLegitimateInterests),
          i.set("purposes", e.vendorConsents),
          i.forEach((s, o) => {
            s.forEach((d, a) => {
              if (d) {
                const r = n.vendors[a];
                if (!r || r.deletedDate) s.unset(a);
                else if (
                  r[o].length === 0 &&
                  !(
                    o === "legIntPurposes" &&
                    r.purposes.length === 0 &&
                    r.legIntPurposes.length === 0 &&
                    r.specialPurposes.length > 0
                  )
                )
                  if (e.isServiceSpecific)
                    if (r.flexiblePurposes.length === 0) s.unset(a);
                    else {
                      const p = e.publisherRestrictions.getRestrictions(a);
                      let l = !1;
                      for (let f = 0, u = p.length; f < u && !l; f++)
                        l =
                          (p[f].restrictionType === q.REQUIRE_CONSENT &&
                            o === "purposes") ||
                          (p[f].restrictionType === q.REQUIRE_LI &&
                            o === "legIntPurposes");
                      l || s.unset(a);
                    }
                  else s.unset(a);
              }
            });
          }),
          e.vendorsDisclosed.set(n.vendors),
          e
        );
      },
    ];
    static process(e, n) {
      const i = e.gvl;
      if (!i) throw new Z("Unable to encode TCModel without a GVL");
      if (!i.isReady)
        throw new Z(
          "Unable to encode TCModel tcModel.gvl.readyPromise is not resolved"
        );
      (e = e.clone()),
        (e.consentLanguage = i.language.slice(0, 2).toUpperCase()),
        n?.version > 0 && n?.version <= this.processor.length
          ? (e.version = n.version)
          : (e.version = this.processor.length);
      const s = e.version - 1;
      if (!this.processor[s]) throw new Z(`Invalid version: ${e.version}`);
      return this.processor[s](e, i);
    }
  }
  class Zs {
    static absCall(e, n, i, s) {
      return new Promise((o, d) => {
        const a = new XMLHttpRequest(),
          r = () => {
            if (a.readyState == XMLHttpRequest.DONE)
              if (a.status >= 200 && a.status < 300) {
                let u = a.response;
                if (typeof u == "string")
                  try {
                    u = JSON.parse(u);
                  } catch {}
                o(u);
              } else
                d(
                  new Error(
                    `HTTP Status: ${a.status} response type: ${a.responseType}`
                  )
                );
          },
          p = () => {
            d(new Error("error"));
          },
          l = () => {
            d(new Error("aborted"));
          },
          f = () => {
            d(new Error("Timeout " + s + "ms " + e));
          };
        (a.withCredentials = i),
          a.addEventListener("load", r),
          a.addEventListener("error", p),
          a.addEventListener("abort", l),
          n === null ? a.open("GET", e, !0) : a.open("POST", e, !0),
          (a.responseType = "json"),
          (a.timeout = s),
          (a.ontimeout = f),
          a.send(n);
      });
    }
    static post(e, n, i = !1, s = 0) {
      return this.absCall(e, JSON.stringify(n), i, s);
    }
    static fetch(e, n = !1, i = 0) {
      return this.absCall(e, null, n, i);
    }
  }
  class x extends Pe {
    static LANGUAGE_CACHE = new Map();
    static CACHE = new Map();
    static LATEST_CACHE_KEY = 0;
    static DEFAULT_LANGUAGE = "EN";
    static consentLanguages = new ee();
    static baseUrl_;
    static set baseUrl(e) {
      if (/^https?:\/\/vendorlist\.consensu\.org\//.test(e))
        throw new Se(
          "Invalid baseUrl!  You may not pull directly from vendorlist.consensu.org and must provide your own cache"
        );
      e.length > 0 && e[e.length - 1] !== "/" && (e += "/"),
        (this.baseUrl_ = e);
    }
    static get baseUrl() {
      return this.baseUrl_;
    }
    static latestFilename = "vendor-list.json";
    static versionedFilename = "archives/vendor-list-v[VERSION].json";
    static languageFilename = "purposes-[LANG].json";
    readyPromise;
    gvlSpecificationVersion;
    vendorListVersion;
    tcfPolicyVersion;
    lastUpdated;
    purposes;
    specialPurposes;
    features;
    specialFeatures;
    isReady_ = !1;
    vendors_;
    vendorIds;
    fullVendorList;
    byPurposeVendorMap;
    bySpecialPurposeVendorMap;
    byFeatureVendorMap;
    bySpecialFeatureVendorMap;
    stacks;
    dataCategories;
    lang_;
    cacheLang_;
    isLatest = !1;
    constructor(e) {
      super();
      let n = x.baseUrl;
      if (
        ((this.lang_ = x.DEFAULT_LANGUAGE),
        (this.cacheLang_ = x.DEFAULT_LANGUAGE),
        this.isVendorList(e))
      )
        this.populate(e), (this.readyPromise = Promise.resolve());
      else {
        if (!n)
          throw new Se("must specify GVL.baseUrl before loading GVL json");
        if (e > 0) {
          const i = e;
          x.CACHE.has(i)
            ? (this.populate(x.CACHE.get(i)),
              (this.readyPromise = Promise.resolve()))
            : ((n += x.versionedFilename.replace("[VERSION]", String(i))),
              (this.readyPromise = this.fetchJson(n)));
        } else
          x.CACHE.has(x.LATEST_CACHE_KEY)
            ? (this.populate(x.CACHE.get(x.LATEST_CACHE_KEY)),
              (this.readyPromise = Promise.resolve()))
            : ((this.isLatest = !0),
              (this.readyPromise = this.fetchJson(n + x.latestFilename)));
      }
    }
    static emptyLanguageCache(e) {
      let n = !1;
      return (
        e == null && x.LANGUAGE_CACHE.size > 0
          ? ((x.LANGUAGE_CACHE = new Map()), (n = !0))
          : typeof e == "string" &&
            this.consentLanguages.has(e.toUpperCase()) &&
            (x.LANGUAGE_CACHE.delete(e.toUpperCase()), (n = !0)),
        n
      );
    }
    static emptyCache(e) {
      let n = !1;
      return (
        Number.isInteger(e) && e >= 0
          ? (x.CACHE.delete(e), (n = !0))
          : e === void 0 && ((x.CACHE = new Map()), (n = !0)),
        n
      );
    }
    cacheLanguage() {
      x.LANGUAGE_CACHE.has(this.cacheLang_) ||
        x.LANGUAGE_CACHE.set(this.cacheLang_, {
          purposes: this.purposes,
          specialPurposes: this.specialPurposes,
          features: this.features,
          specialFeatures: this.specialFeatures,
          stacks: this.stacks,
          dataCategories: this.dataCategories,
        });
    }
    async fetchJson(e) {
      try {
        this.populate(await Zs.fetch(e));
      } catch (n) {
        throw new Se(n.message);
      }
    }
    getJson() {
      return JSON.parse(
        JSON.stringify({
          gvlSpecificationVersion: this.gvlSpecificationVersion,
          vendorListVersion: this.vendorListVersion,
          tcfPolicyVersion: this.tcfPolicyVersion,
          lastUpdated: this.lastUpdated,
          purposes: this.purposes,
          specialPurposes: this.specialPurposes,
          features: this.features,
          specialFeatures: this.specialFeatures,
          stacks: this.stacks,
          dataCategories: this.dataCategories,
          vendors: this.fullVendorList,
        })
      );
    }
    async changeLanguage(e) {
      let n = e;
      try {
        n = x.consentLanguages.parseLanguage(e);
      } catch (s) {
        throw new Se("Error during parsing the language: " + s.message);
      }
      const i = e.toUpperCase();
      if (
        !(
          n.toLowerCase() === x.DEFAULT_LANGUAGE.toLowerCase() &&
          !x.LANGUAGE_CACHE.has(i)
        ) &&
        n !== this.lang_
      )
        if (((this.lang_ = n), x.LANGUAGE_CACHE.has(i))) {
          const s = x.LANGUAGE_CACHE.get(i);
          for (const o in s) s.hasOwnProperty(o) && (this[o] = s[o]);
        } else {
          const s =
            x.baseUrl +
            x.languageFilename.replace("[LANG]", this.lang_.toLowerCase());
          try {
            await this.fetchJson(s),
              (this.cacheLang_ = i),
              this.cacheLanguage();
          } catch (o) {
            throw new Se("unable to load language: " + o.message);
          }
        }
    }
    get language() {
      return this.lang_;
    }
    isVendorList(e) {
      return e !== void 0 && e.vendors !== void 0;
    }
    populate(e) {
      (this.purposes = e.purposes),
        (this.specialPurposes = e.specialPurposes),
        (this.features = e.features),
        (this.specialFeatures = e.specialFeatures),
        (this.stacks = e.stacks),
        (this.dataCategories = e.dataCategories),
        this.isVendorList(e) &&
          ((this.gvlSpecificationVersion = e.gvlSpecificationVersion),
          (this.tcfPolicyVersion = e.tcfPolicyVersion),
          (this.vendorListVersion = e.vendorListVersion),
          (this.lastUpdated = e.lastUpdated),
          typeof this.lastUpdated == "string" &&
            (this.lastUpdated = new Date(this.lastUpdated)),
          (this.vendors_ = e.vendors),
          (this.fullVendorList = e.vendors),
          this.mapVendors(),
          (this.isReady_ = !0),
          this.isLatest && x.CACHE.set(x.LATEST_CACHE_KEY, this.getJson()),
          x.CACHE.has(this.vendorListVersion) ||
            x.CACHE.set(this.vendorListVersion, this.getJson())),
        this.cacheLanguage();
    }
    mapVendors(e) {
      (this.byPurposeVendorMap = {}),
        (this.bySpecialPurposeVendorMap = {}),
        (this.byFeatureVendorMap = {}),
        (this.bySpecialFeatureVendorMap = {}),
        Object.keys(this.purposes).forEach((n) => {
          this.byPurposeVendorMap[n] = {
            legInt: new Set(),
            consent: new Set(),
            flexible: new Set(),
          };
        }),
        Object.keys(this.specialPurposes).forEach((n) => {
          this.bySpecialPurposeVendorMap[n] = new Set();
        }),
        Object.keys(this.features).forEach((n) => {
          this.byFeatureVendorMap[n] = new Set();
        }),
        Object.keys(this.specialFeatures).forEach((n) => {
          this.bySpecialFeatureVendorMap[n] = new Set();
        }),
        Array.isArray(e) ||
          (e = Object.keys(this.fullVendorList).map((n) => +n)),
        (this.vendorIds = new Set(e)),
        (this.vendors_ = e.reduce((n, i) => {
          const s = this.vendors_[String(i)];
          return (
            s &&
              s.deletedDate === void 0 &&
              (s.purposes.forEach((o) => {
                this.byPurposeVendorMap[String(o)].consent.add(i);
              }),
              s.specialPurposes.forEach((o) => {
                this.bySpecialPurposeVendorMap[String(o)].add(i);
              }),
              s.legIntPurposes.forEach((o) => {
                this.byPurposeVendorMap[String(o)].legInt.add(i);
              }),
              s.flexiblePurposes &&
                s.flexiblePurposes.forEach((o) => {
                  this.byPurposeVendorMap[String(o)].flexible.add(i);
                }),
              s.features.forEach((o) => {
                this.byFeatureVendorMap[String(o)].add(i);
              }),
              s.specialFeatures.forEach((o) => {
                this.bySpecialFeatureVendorMap[String(o)].add(i);
              }),
              (n[i] = s)),
            n
          );
        }, {}));
    }
    getFilteredVendors(e, n, i, s) {
      const o = e.charAt(0).toUpperCase() + e.slice(1);
      let d;
      const a = {};
      return (
        e === "purpose" && i
          ? (d = this["by" + o + "VendorMap"][String(n)][i])
          : (d =
              this["by" + (s ? "Special" : "") + o + "VendorMap"][String(n)]),
        d.forEach((r) => {
          a[String(r)] = this.vendors[String(r)];
        }),
        a
      );
    }
    getVendorsWithConsentPurpose(e) {
      return this.getFilteredVendors("purpose", e, "consent");
    }
    getVendorsWithLegIntPurpose(e) {
      return this.getFilteredVendors("purpose", e, "legInt");
    }
    getVendorsWithFlexiblePurpose(e) {
      return this.getFilteredVendors("purpose", e, "flexible");
    }
    getVendorsWithSpecialPurpose(e) {
      return this.getFilteredVendors("purpose", e, void 0, !0);
    }
    getVendorsWithFeature(e) {
      return this.getFilteredVendors("feature", e);
    }
    getVendorsWithSpecialFeature(e) {
      return this.getFilteredVendors("feature", e, void 0, !0);
    }
    get vendors() {
      return this.vendors_;
    }
    narrowVendorsTo(e) {
      this.mapVendors(e);
    }
    get isReady() {
      return this.isReady_;
    }
    clone() {
      const e = new x(this.getJson());
      return (
        this.lang_ !== x.DEFAULT_LANGUAGE && e.changeLanguage(this.lang_), e
      );
    }
    static isInstanceOf(e) {
      return typeof e == "object" && typeof e.narrowVendorsTo == "function";
    }
  }
  class pt extends Pe {
    static consentLanguages = x.consentLanguages;
    isServiceSpecific_ = !1;
    supportOOB_ = !0;
    useNonStandardTexts_ = !1;
    purposeOneTreatment_ = !1;
    publisherCountryCode_ = "AA";
    version_ = 2;
    consentScreen_ = 0;
    policyVersion_ = 4;
    consentLanguage_ = "EN";
    cmpId_ = 0;
    cmpVersion_ = 0;
    vendorListVersion_ = 0;
    numCustomPurposes_ = 0;
    gvl_;
    created;
    lastUpdated;
    specialFeatureOptins = new D();
    purposeConsents = new D();
    purposeLegitimateInterests = new D();
    publisherConsents = new D();
    publisherLegitimateInterests = new D();
    publisherCustomConsents = new D();
    publisherCustomLegitimateInterests = new D();
    customPurposes;
    vendorConsents = new D();
    vendorLegitimateInterests = new D();
    vendorsDisclosed = new D();
    vendorsAllowed = new D();
    publisherRestrictions = new Gt();
    constructor(e) {
      super(), e && (this.gvl = e), this.updated();
    }
    set gvl(e) {
      x.isInstanceOf(e) || (e = new x(e)),
        (this.gvl_ = e),
        (this.publisherRestrictions.gvl = e);
    }
    get gvl() {
      return this.gvl_;
    }
    set cmpId(e) {
      if (((e = Number(e)), Number.isInteger(e) && e > 1)) this.cmpId_ = e;
      else throw new X("cmpId", e);
    }
    get cmpId() {
      return this.cmpId_;
    }
    set cmpVersion(e) {
      if (((e = Number(e)), Number.isInteger(e) && e > -1))
        this.cmpVersion_ = e;
      else throw new X("cmpVersion", e);
    }
    get cmpVersion() {
      return this.cmpVersion_;
    }
    set consentScreen(e) {
      if (((e = Number(e)), Number.isInteger(e) && e > -1))
        this.consentScreen_ = e;
      else throw new X("consentScreen", e);
    }
    get consentScreen() {
      return this.consentScreen_;
    }
    set consentLanguage(e) {
      this.consentLanguage_ = e;
    }
    get consentLanguage() {
      return this.consentLanguage_;
    }
    set publisherCountryCode(e) {
      if (/^([A-z]){2}$/.test(e)) this.publisherCountryCode_ = e.toUpperCase();
      else throw new X("publisherCountryCode", e);
    }
    get publisherCountryCode() {
      return this.publisherCountryCode_;
    }
    set vendorListVersion(e) {
      if (((e = Number(e) >> 0), e < 0)) throw new X("vendorListVersion", e);
      this.vendorListVersion_ = e;
    }
    get vendorListVersion() {
      return this.gvl ? this.gvl.vendorListVersion : this.vendorListVersion_;
    }
    set policyVersion(e) {
      if (((this.policyVersion_ = parseInt(e, 10)), this.policyVersion_ < 0))
        throw new X("policyVersion", e);
    }
    get policyVersion() {
      return this.gvl ? this.gvl.tcfPolicyVersion : this.policyVersion_;
    }
    set version(e) {
      this.version_ = parseInt(e, 10);
    }
    get version() {
      return this.version_;
    }
    set isServiceSpecific(e) {
      this.isServiceSpecific_ = e;
    }
    get isServiceSpecific() {
      return this.isServiceSpecific_;
    }
    set useNonStandardTexts(e) {
      this.useNonStandardTexts_ = e;
    }
    get useNonStandardTexts() {
      return this.useNonStandardTexts_;
    }
    set supportOOB(e) {
      this.supportOOB_ = e;
    }
    get supportOOB() {
      return this.supportOOB_;
    }
    set purposeOneTreatment(e) {
      this.purposeOneTreatment_ = e;
    }
    get purposeOneTreatment() {
      return this.purposeOneTreatment_;
    }
    setAllVendorConsents() {
      this.vendorConsents.set(this.gvl.vendors);
    }
    unsetAllVendorConsents() {
      this.vendorConsents.empty();
    }
    setAllVendorsDisclosed() {
      this.vendorsDisclosed.set(this.gvl.vendors);
    }
    unsetAllVendorsDisclosed() {
      this.vendorsDisclosed.empty();
    }
    setAllVendorsAllowed() {
      this.vendorsAllowed.set(this.gvl.vendors);
    }
    unsetAllVendorsAllowed() {
      this.vendorsAllowed.empty();
    }
    setAllVendorLegitimateInterests() {
      this.vendorLegitimateInterests.set(this.gvl.vendors);
    }
    unsetAllVendorLegitimateInterests() {
      this.vendorLegitimateInterests.empty();
    }
    setAllPurposeConsents() {
      this.purposeConsents.set(this.gvl.purposes);
    }
    unsetAllPurposeConsents() {
      this.purposeConsents.empty();
    }
    setAllPurposeLegitimateInterests() {
      this.purposeLegitimateInterests.set(this.gvl.purposes);
    }
    unsetAllPurposeLegitimateInterests() {
      this.purposeLegitimateInterests.empty();
    }
    setAllSpecialFeatureOptins() {
      this.specialFeatureOptins.set(this.gvl.specialFeatures);
    }
    unsetAllSpecialFeatureOptins() {
      this.specialFeatureOptins.empty();
    }
    setAll() {
      this.setAllVendorConsents(),
        this.setAllPurposeLegitimateInterests(),
        this.setAllSpecialFeatureOptins(),
        this.setAllPurposeConsents(),
        this.setAllVendorLegitimateInterests();
    }
    unsetAll() {
      this.unsetAllVendorConsents(),
        this.unsetAllPurposeLegitimateInterests(),
        this.unsetAllSpecialFeatureOptins(),
        this.unsetAllPurposeConsents(),
        this.unsetAllVendorLegitimateInterests();
    }
    get numCustomPurposes() {
      let e = this.numCustomPurposes_;
      if (typeof this.customPurposes == "object") {
        const n = Object.keys(this.customPurposes).sort(
          (i, s) => Number(i) - Number(s)
        );
        e = parseInt(n.pop(), 10);
      }
      return e;
    }
    set numCustomPurposes(e) {
      if (
        ((this.numCustomPurposes_ = parseInt(e, 10)),
        this.numCustomPurposes_ < 0)
      )
        throw new X("numCustomPurposes", e);
    }
    updated() {
      const e = new Date(),
        n = new Date(
          Date.UTC(e.getUTCFullYear(), e.getUTCMonth(), e.getUTCDate())
        );
      (this.created = n), (this.lastUpdated = n);
    }
  }
  class Ve {
    static encode(e, n) {
      let i = "",
        s;
      return (
        (e = Js.process(e, n)),
        Array.isArray(n?.segments)
          ? (s = n.segments)
          : (s = new Qs(e, n)["" + e.version]),
        s.forEach((o, d) => {
          let a = "";
          d < s.length - 1 && (a = "."), (i += Jt.encode(e, o) + a);
        }),
        i
      );
    }
    static decode(e, n) {
      const i = e.split("."),
        s = i.length;
      n || (n = new pt());
      for (let o = 0; o < s; o++) {
        const d = i[o],
          r = ct.decode(d.charAt(0)).substr(0, _.segmentType),
          p = Yt.ID_TO_KEY[I.decode(r, _.segmentType).toString()];
        Jt.decode(d, n, p);
      }
      return n;
    }
  }
  const ut = (t) => {
      var e;
      const n = (e = window.dataLayer) != null ? e : [];
      window.dataLayer = n;
      const i = { consent: t.detail.consent };
      n.push({ event: t.type, Fides: i });
    },
    Zt = () => {
      var t;
      window.addEventListener("FidesInitialized", (e) => ut(e)),
        window.addEventListener("FidesUpdated", (e) => ut(e)),
        (t = window.Fides) != null &&
          t.initialized &&
          ut({
            type: "FidesInitialized",
            detail: {
              consent: window.Fides.consent,
              fides_meta: window.Fides.fides_meta,
              identity: window.Fides.identity,
              tcf_consent: window.Fides.tcf_consent,
            },
          });
    },
    Xs = () => {
      if (window.fbq) return window.fbq;
      const t = {
        queue: [],
        loaded: !0,
        version: "2.0",
        push(...e) {
          const n = window.fbq;
          n.callMethod ? n.callMethod(...e) : n.queue.push(e);
        },
      };
      return (
        (window.fbq = Object.assign(t.push, t)),
        (window._fbq = window.fbq),
        window.fbq
      );
    },
    Xt = (t) => {
      const e = Xs();
      e("consent", t.consent ? "grant" : "revoke"),
        t.dataUse
          ? e("dataProcessingOptions", [])
          : e("dataProcessingOptions", ["LDU"], 1, 1e3);
    },
    en = (t) => {
      var e;
      if (!((e = window.Shopify) != null && e.customerPrivacy))
        throw Error("Fides could not access Shopify's customerPrivacy API");
      window.Shopify.customerPrivacy.setTrackingConsent(!!t.tracking, () => {});
    },
    tn = (t) => {
      if (!window.Shopify)
        throw Error(
          "Fides.shopify was called but Shopify is not present in the page."
        );
      if (window.Shopify.customerPrivacy) {
        en(t);
        return;
      }
      window.Shopify.loadFeatures(
        [{ name: "consent-tracking-api", version: "0.1" }],
        (e) => {
          if (e)
            throw Error("Fides could not load Shopify's consent-tracking-api");
          en(t);
        }
      );
    };
  var N;
  (function (t) {
    (t.PING = "ping"),
      (t.GET_TC_DATA = "getTCData"),
      (t.GET_IN_APP_TC_DATA = "getInAppTCData"),
      (t.GET_VENDOR_LIST = "getVendorList"),
      (t.ADD_EVENT_LISTENER = "addEventListener"),
      (t.REMOVE_EVENT_LISTENER = "removeEventListener");
  })(N || (N = {}));
  var ce;
  (function (t) {
    (t.STUB = "stub"),
      (t.LOADING = "loading"),
      (t.LOADED = "loaded"),
      (t.ERROR = "error");
  })(ce || (ce = {}));
  var pe;
  (function (t) {
    (t.VISIBLE = "visible"), (t.HIDDEN = "hidden"), (t.DISABLED = "disabled");
  })(pe || (pe = {}));
  var Ae;
  (function (t) {
    (t.TC_LOADED = "tcloaded"),
      (t.CMP_UI_SHOWN = "cmpuishown"),
      (t.USER_ACTION_COMPLETE = "useractioncomplete");
  })(Ae || (Ae = {}));
  class De {
    listenerId;
    callback;
    next;
    param;
    success = !0;
    constructor(e, n, i, s) {
      Object.assign(this, { callback: e, listenerId: i, param: n, next: s });
      try {
        this.respond();
      } catch {
        this.invokeCallback(null);
      }
    }
    invokeCallback(e) {
      const n = e !== null;
      typeof this.next == "function"
        ? this.callback(this.next, e, n)
        : this.callback(e, n);
    }
  }
  class Ue extends De {
    respond() {
      this.throwIfParamInvalid(),
        this.invokeCallback(new nn(this.param, this.listenerId));
    }
    throwIfParamInvalid() {
      if (
        this.param !== void 0 &&
        (!Array.isArray(this.param) || !this.param.every(Number.isInteger))
      )
        throw new Error("Invalid Parameter");
    }
  }
  class eo {
    eventQueue = new Map();
    queueNumber = 0;
    add(e) {
      return this.eventQueue.set(this.queueNumber, e), this.queueNumber++;
    }
    remove(e) {
      return this.eventQueue.delete(e);
    }
    exec() {
      this.eventQueue.forEach((e, n) => {
        new Ue(e.callback, e.param, n, e.next);
      });
    }
    clear() {
      (this.queueNumber = 0), this.eventQueue.clear();
    }
    get size() {
      return this.eventQueue.size;
    }
  }
  class w {
    static apiVersion = "2";
    static tcfPolicyVersion;
    static eventQueue = new eo();
    static cmpStatus = ce.LOADING;
    static disabled = !1;
    static displayStatus = pe.HIDDEN;
    static cmpId;
    static cmpVersion;
    static eventStatus;
    static gdprApplies;
    static tcModel;
    static tcString;
    static reset() {
      delete this.cmpId,
        delete this.cmpVersion,
        delete this.eventStatus,
        delete this.gdprApplies,
        delete this.tcModel,
        delete this.tcString,
        delete this.tcfPolicyVersion,
        (this.cmpStatus = ce.LOADING),
        (this.disabled = !1),
        (this.displayStatus = pe.HIDDEN),
        this.eventQueue.clear();
    }
  }
  class ft {
    cmpId = w.cmpId;
    cmpVersion = w.cmpVersion;
    gdprApplies = w.gdprApplies;
    tcfPolicyVersion = w.tcfPolicyVersion;
  }
  class to extends ft {
    cmpStatus = ce.ERROR;
  }
  class nn extends ft {
    tcString;
    listenerId;
    eventStatus;
    cmpStatus;
    isServiceSpecific;
    useNonStandardStacks;
    publisherCC;
    purposeOneTreatment;
    outOfBand;
    purpose;
    vendor;
    specialFeatureOptins;
    publisher;
    constructor(e, n) {
      if (
        (super(),
        (this.eventStatus = w.eventStatus),
        (this.cmpStatus = w.cmpStatus),
        (this.listenerId = n),
        w.gdprApplies)
      ) {
        const i = w.tcModel;
        (this.tcString = w.tcString),
          (this.isServiceSpecific = i.isServiceSpecific),
          (this.useNonStandardStacks = i.useNonStandardStacks),
          (this.purposeOneTreatment = i.purposeOneTreatment),
          (this.publisherCC = i.publisherCountryCode),
          (this.outOfBand = {
            allowedVendors: this.createVectorField(i.vendorsAllowed, e),
            disclosedVendors: this.createVectorField(i.vendorsDisclosed, e),
          }),
          (this.purpose = {
            consents: this.createVectorField(i.purposeConsents),
            legitimateInterests: this.createVectorField(
              i.purposeLegitimateInterests
            ),
          }),
          (this.vendor = {
            consents: this.createVectorField(i.vendorConsents, e),
            legitimateInterests: this.createVectorField(
              i.vendorLegitimateInterests,
              e
            ),
          }),
          (this.specialFeatureOptins = this.createVectorField(
            i.specialFeatureOptins
          )),
          (this.publisher = {
            consents: this.createVectorField(i.publisherConsents),
            legitimateInterests: this.createVectorField(
              i.publisherLegitimateInterests
            ),
            customPurpose: {
              consents: this.createVectorField(i.publisherCustomConsents),
              legitimateInterests: this.createVectorField(
                i.publisherCustomLegitimateInterests
              ),
            },
            restrictions: this.createRestrictions(i.publisherRestrictions),
          });
      }
    }
    createRestrictions(e) {
      const n = {};
      if (e.numRestrictions > 0) {
        const i = e.getMaxVendorId();
        for (let s = 1; s <= i; s++) {
          const o = s.toString();
          e.getRestrictions(s).forEach((d) => {
            const a = d.purposeId.toString();
            n[a] || (n[a] = {}), (n[a][o] = d.restrictionType);
          });
        }
      }
      return n;
    }
    createVectorField(e, n) {
      return n
        ? n.reduce((i, s) => ((i[String(s)] = e.has(Number(s))), i), {})
        : [...e].reduce((i, s) => ((i[s[0].toString(10)] = s[1]), i), {});
    }
  }
  class no extends nn {
    constructor(e) {
      super(e), delete this.outOfBand;
    }
    createVectorField(e) {
      return [...e].reduce((n, i) => ((n += i[1] ? "1" : "0"), n), "");
    }
    createRestrictions(e) {
      const n = {};
      if (e.numRestrictions > 0) {
        const i = e.getMaxVendorId();
        e.getRestrictions().forEach((s) => {
          n[s.purposeId.toString()] = "_".repeat(i);
        });
        for (let s = 0; s < i; s++) {
          const o = s + 1;
          e.getRestrictions(o).forEach((d) => {
            const a = d.restrictionType.toString(),
              r = d.purposeId.toString(),
              p = n[r].substr(0, s),
              l = n[r].substr(s + 1);
            n[r] = p + a + l;
          });
        }
      }
      return n;
    }
  }
  class io extends ft {
    cmpLoaded = !0;
    cmpStatus = w.cmpStatus;
    displayStatus = w.displayStatus;
    apiVersion = String(w.apiVersion);
    gvlVersion;
    constructor() {
      super(),
        w.tcModel &&
          w.tcModel.vendorListVersion &&
          (this.gvlVersion = +w.tcModel.vendorListVersion);
    }
  }
  class so extends De {
    respond() {
      this.invokeCallback(new io());
    }
  }
  class oo extends Ue {
    respond() {
      this.throwIfParamInvalid(), this.invokeCallback(new no(this.param));
    }
  }
  class ro extends De {
    respond() {
      const e = w.tcModel,
        n = e.vendorListVersion;
      let i;
      this.param === void 0 && (this.param = n),
        this.param === n && e.gvl ? (i = e.gvl) : (i = new x(this.param)),
        i.readyPromise.then(() => {
          this.invokeCallback(i.getJson());
        });
    }
  }
  class ao extends Ue {
    respond() {
      (this.listenerId = w.eventQueue.add({
        callback: this.callback,
        param: this.param,
        next: this.next,
      })),
        super.respond();
    }
  }
  class lo extends De {
    respond() {
      this.invokeCallback(w.eventQueue.remove(this.param));
    }
  }
  class Le {
    static [N.PING] = so;
    static [N.GET_TC_DATA] = Ue;
    static [N.GET_IN_APP_TC_DATA] = oo;
    static [N.GET_VENDOR_LIST] = ro;
    static [N.ADD_EVENT_LISTENER] = ao;
    static [N.REMOVE_EVENT_LISTENER] = lo;
  }
  class co {
    static set_ = new Set([0, 2, void 0, null]);
    static has(e) {
      return typeof e == "string" && (e = Number(e)), this.set_.has(e);
    }
  }
  const gt = "__tcfapi";
  class po {
    callQueue;
    customCommands;
    constructor(e) {
      if (e) {
        let n = N.ADD_EVENT_LISTENER;
        if (e?.[n])
          throw new Error(
            `Built-In Custom Commmand for ${n} not allowed: Use ${N.GET_TC_DATA} instead`
          );
        if (((n = N.REMOVE_EVENT_LISTENER), e?.[n]))
          throw new Error(`Built-In Custom Commmand for ${n} not allowed`);
        e?.[N.GET_TC_DATA] &&
          ((e[N.ADD_EVENT_LISTENER] = e[N.GET_TC_DATA]),
          (e[N.REMOVE_EVENT_LISTENER] = e[N.GET_TC_DATA])),
          (this.customCommands = e);
      }
      try {
        this.callQueue = window[gt]() || [];
      } catch {
        this.callQueue = [];
      } finally {
        (window[gt] = this.apiCall.bind(this)), this.purgeQueuedCalls();
      }
    }
    apiCall(e, n, i, ...s) {
      if (typeof e != "string") i(null, !1);
      else if (!co.has(n)) i(null, !1);
      else {
        if (typeof i != "function")
          throw new Error("invalid callback function");
        w.disabled
          ? i(new to(), !1)
          : !this.isCustomCommand(e) && !this.isBuiltInCommand(e)
          ? i(null, !1)
          : this.isCustomCommand(e) && !this.isBuiltInCommand(e)
          ? this.customCommands[e](i, ...s)
          : e === N.PING
          ? this.isCustomCommand(e)
            ? new Le[e](this.customCommands[e], s[0], null, i)
            : new Le[e](i, s[0])
          : w.tcModel === void 0
          ? this.callQueue.push([e, n, i, ...s])
          : this.isCustomCommand(e) && this.isBuiltInCommand(e)
          ? new Le[e](this.customCommands[e], s[0], null, i)
          : new Le[e](i, s[0]);
      }
    }
    purgeQueuedCalls() {
      const e = this.callQueue;
      (this.callQueue = []),
        e.forEach((n) => {
          window[gt](...n);
        });
    }
    isCustomCommand(e) {
      return this.customCommands && typeof this.customCommands[e] == "function";
    }
    isBuiltInCommand(e) {
      return Le[e] !== void 0;
    }
  }
  class uo {
    callResponder;
    isServiceSpecific;
    numUpdates = 0;
    constructor(e, n, i = !1, s) {
      this.throwIfInvalidInt(e, "cmpId", 2),
        this.throwIfInvalidInt(n, "cmpVersion", 0),
        (w.cmpId = e),
        (w.cmpVersion = n),
        (w.tcfPolicyVersion = 2),
        (this.isServiceSpecific = !!i),
        (this.callResponder = new po(s));
    }
    throwIfInvalidInt(e, n, i) {
      if (!(typeof e == "number" && Number.isInteger(e) && e >= i))
        throw new Error(`Invalid ${n}: ${e}`);
    }
    update(e, n = !1) {
      if (w.disabled) throw new Error("CmpApi Disabled");
      (w.cmpStatus = ce.LOADED),
        n
          ? ((w.displayStatus = pe.VISIBLE), (w.eventStatus = Ae.CMP_UI_SHOWN))
          : w.tcModel === void 0
          ? ((w.displayStatus = pe.DISABLED), (w.eventStatus = Ae.TC_LOADED))
          : ((w.displayStatus = pe.HIDDEN),
            (w.eventStatus = Ae.USER_ACTION_COMPLETE)),
        (w.gdprApplies = e !== null),
        w.gdprApplies
          ? (e === ""
              ? ((w.tcModel = new pt()),
                (w.tcModel.cmpId = w.cmpId),
                (w.tcModel.cmpVersion = w.cmpVersion))
              : (w.tcModel = Ve.decode(e)),
            (w.tcModel.isServiceSpecific = this.isServiceSpecific),
            (w.tcfPolicyVersion = Number(w.tcModel.policyVersion)),
            (w.tcString = e))
          : (w.tcModel = null),
        this.numUpdates === 0
          ? this.callResponder.purgeQueuedCalls()
          : w.eventQueue.exec(),
        this.numUpdates++;
    }
    disable() {
      (w.disabled = !0), (w.cmpStatus = ce.ERROR);
    }
  }
  var fo = Object.defineProperty,
    go = Object.defineProperties,
    vo = Object.getOwnPropertyDescriptors,
    sn = Object.getOwnPropertySymbols,
    ho = Object.prototype.hasOwnProperty,
    bo = Object.prototype.propertyIsEnumerable,
    on = (t, e, n) =>
      e in t
        ? fo(t, e, { enumerable: !0, configurable: !0, writable: !0, value: n })
        : (t[e] = n),
    vt = (t, e) => {
      for (var n in e || (e = {})) ho.call(e, n) && on(t, n, e[n]);
      if (sn) for (var n of sn(e)) bo.call(e, n) && on(t, n, e[n]);
      return t;
    },
    _o = (t, e) => go(t, vo(e)),
    rn = ((t) => ((t.GVL = "gvl"), (t.AC = "gacp"), t))(rn || {});
  const be = (t) => {
      const e = t.split(".");
      return e.length === 1
        ? { source: void 0, id: e[0] }
        : { source: e[0], id: e[1] };
    },
    _e = (t, e) => {
      if (!e) return;
      const { source: n, id: i } = be(t);
      if (n === "gvl" || n === void 0) return e.vendors[i];
    },
    mo = (t) => be(t).source === "gacp",
    yo = (t) => {
      const { tcf_vendor_relationships: e = [] } = t;
      return e
        .map((n) => n.id)
        .filter((n) => _e(n, t.gvl))
        .map((n) => +be(n).id);
    },
    an = ({
      consents: t,
      legints: e,
      relationships: n,
      isFidesSystem: i,
      gvl: s,
    }) => {
      const o = [];
      return (
        n.forEach((d) => {
          const a = t.find((l) => l.id === d.id),
            r = e.find((l) => l.id === d.id),
            p = _o(vt(vt(vt({}, d), a), r), {
              isFidesSystem: i,
              isConsent: !!a,
              isLegint: !!r,
              isGvl: !!_e(d.id, s),
            });
          o.push(p);
        }),
        o
      );
    },
    wo = (t) => {
      const {
          tcf_vendor_consents: e = [],
          tcf_vendor_legitimate_interests: n = [],
          tcf_vendor_relationships: i = [],
          tcf_system_consents: s = [],
          tcf_system_legitimate_interests: o = [],
          tcf_system_relationships: d = [],
        } = t,
        a = an({
          consents: e,
          legints: n,
          relationships: i,
          isFidesSystem: !1,
          gvl: t.gvl,
        }),
        r = an({
          consents: s,
          legints: o,
          relationships: d,
          isFidesSystem: !0,
          gvl: t.gvl,
        });
      return [...a, ...r];
    };
  var Co = ((t) => (
      (t.CONSENT = "Consent"),
      (t.CONTRACT = "Contract"),
      (t.LEGAL_OBLIGATIONS = "Legal obligations"),
      (t.VITAL_INTERESTS = "Vital interests"),
      (t.PUBLIC_INTEREST = "Public interest"),
      (t.LEGITIMATE_INTERESTS = "Legitimate interests"),
      t
    ))(Co || {}),
    te = ((t) => (
      (t.CONSENT = "Consent"),
      (t.LEGITIMATE_INTERESTS = "Legitimate interests"),
      t
    ))(te || {});
  const dn = 407,
    Me = ",",
    ln = [
      {
        experienceKey: "tcf_purpose_consents",
        tcfModelKey: "purposeConsents",
        enabledIdsKey: "purposesConsent",
      },
      {
        experienceKey: "tcf_purpose_legitimate_interests",
        tcfModelKey: "purposeLegitimateInterests",
        enabledIdsKey: "purposesLegint",
      },
      {
        experienceKey: "tcf_special_features",
        tcfModelKey: "specialFeatureOptins",
        enabledIdsKey: "specialFeatures",
      },
      {
        experienceKey: "tcf_vendor_consents",
        tcfModelKey: "vendorConsents",
        enabledIdsKey: "vendorsConsent",
      },
      {
        experienceKey: "tcf_vendor_legitimate_interests",
        tcfModelKey: "vendorLegitimateInterests",
        enabledIdsKey: "vendorsLegint",
      },
    ],
    cn = [
      {
        cookieKey: "system_consent_preferences",
        experienceKey: "tcf_system_consents",
      },
      {
        cookieKey: "system_legitimate_interests_preferences",
        experienceKey: "tcf_system_legitimate_interests",
      },
    ];
  ln.filter(
    ({ experienceKey: t }) =>
      t !== "tcf_features" && t !== "tcf_special_purposes"
  ).map((t) => t.experienceKey);
  const je = [
      { label: "Consent", value: te.CONSENT },
      { label: "Legitimate interest", value: te.LEGITIMATE_INTERESTS },
    ],
    Be = (t) => {
      if (!window.Fides.options.fidesTcfGdprApplies) return null;
      const { fides_string: e } = t.detail;
      if (e) {
        const [n] = e.split(Me);
        return n.split(".")[0];
      }
      return e ?? "";
    };
  var Eo = Object.defineProperty,
    Io = Object.defineProperties,
    xo = Object.getOwnPropertyDescriptors,
    pn = Object.getOwnPropertySymbols,
    Oo = Object.prototype.hasOwnProperty,
    So = Object.prototype.propertyIsEnumerable,
    un = (t, e, n) =>
      e in t
        ? Eo(t, e, { enumerable: !0, configurable: !0, writable: !0, value: n })
        : (t[e] = n),
    Po = (t, e) => {
      for (var n in e || (e = {})) Oo.call(e, n) && un(t, n, e[n]);
      if (pn) for (var n of pn(e)) So.call(e, n) && un(t, n, e[n]);
      return t;
    },
    To = (t, e) => Io(t, xo(e)),
    ko = (t, e, n) =>
      new Promise((i, s) => {
        var o = (r) => {
            try {
              a(n.next(r));
            } catch (p) {
              s(p);
            }
          },
          d = (r) => {
            try {
              a(n.throw(r));
            } catch (p) {
              s(p);
            }
          },
          a = (r) =>
            r.done ? i(r.value) : Promise.resolve(r.value).then(o, d);
        a((n = n.apply(t, e)).next());
      });
  const fn = 1,
    gn = [1, 3, 4, 5, 6],
    Ao = 1,
    Lo = ({ tcStringPreferences: t }) => {
      const e = Array.from(
        new Set(
          [...t.vendorsConsent, ...t.vendorsLegint]
            .filter((n) => mo(n))
            .map((n) => be(n).id)
        )
      )
        .sort((n, i) => Number(n) - Number(i))
        .join(".");
      return `${Ao}~${e}`;
    },
    No = (t) =>
      ko(void 0, [t], function* ({ experience: e, tcStringPreferences: n }) {
        let i = "";
        try {
          const s = new pt(new x(e.gvl));
          if (
            (yield s.gvl.readyPromise,
            (s.cmpId = dn),
            (s.cmpVersion = fn),
            (s.consentScreen = 1),
            (s.isServiceSpecific = !0),
            (s.supportOOB = !1),
            s.gvl.narrowVendorsTo(yo(e)),
            n)
          ) {
            n.vendorsConsent.forEach((d) => {
              if (_e(d, e.gvl)) {
                const { id: a } = be(d);
                s.vendorConsents.set(+a);
              }
            }),
              n.vendorsLegint.forEach((d) => {
                var a;
                if (_e(d, e.gvl)) {
                  const r =
                      (a = e.tcf_vendor_legitimate_interests) == null
                        ? void 0
                        : a.filter((f) => f.id === d)[0],
                    p = r?.purpose_legitimate_interests;
                  let l = !1;
                  if (
                    p &&
                    (p.map((f) => f.id).filter((f) => gn.includes(f)).length &&
                      (l = !0),
                    !l)
                  ) {
                    const { id: f } = be(d);
                    s.vendorLegitimateInterests.set(+f);
                  }
                }
              }),
              n.purposesConsent.forEach((d) => {
                s.purposeConsents.set(+d);
              }),
              n.purposesLegint.forEach((d) => {
                const a = +d;
                gn.includes(a) || s.purposeLegitimateInterests.set(a);
              }),
              n.specialFeatures.forEach((d) => {
                s.specialFeatureOptins.set(+d);
              }),
              (i = Ve.encode(s, { segments: [P.CORE, P.VENDORS_DISCLOSED] }));
            const o = Lo({ tcStringPreferences: n });
            i = `${i}${Me}${o}`;
          }
        } catch (s) {
          return (
            console.error("Unable to instantiate GVL: ", s), Promise.resolve("")
          );
        }
        return Promise.resolve(i);
      }),
    $o = () => {
      const t = new uo(dn, fn, !0, {
        getTCData: (e, n, i) => {
          var s;
          if (typeof n != "boolean") {
            const o =
                (s = window.Fides.fides_string) == null ? void 0 : s.split(Me),
              d = o?.length === 2 ? o[1] : "";
            e(To(Po({}, n), { addtlConsent: d }), i);
            return;
          }
          e(n, i);
        },
      });
      window.addEventListener("FidesInitialized", (e) => {
        const n = Be(e);
        t.update(n, !1);
      }),
        window.addEventListener("FidesUIShown", (e) => {
          const n = Be(e);
          t.update(n, !0);
        }),
        window.addEventListener("FidesModalClosed", (e) => {
          const n = Be(e);
          t.update(n, !1);
        }),
        window.addEventListener("FidesUpdated", (e) => {
          const n = Be(e);
          t.update(n, !1);
        });
    },
    Fo = () => {
      var t;
      if (window.Fides.options.tcfEnabled) return !1;
      if (
        typeof ((t = window.navigator) == null
          ? void 0
          : t.globalPrivacyControl) == "boolean"
      )
        return window.navigator.globalPrivacyControl;
      const e = new URL(window.location.href).searchParams.get(
        "globalPrivacyControl"
      );
      if (e === "true") return !0;
      if (e === "false") return !1;
    },
    ae = () => (typeof window > "u" ? {} : { globalPrivacyControl: Fo() });
  let He;
  const Ro = new Uint8Array(16);
  function Vo() {
    if (
      !He &&
      ((He =
        typeof crypto < "u" &&
        crypto.getRandomValues &&
        crypto.getRandomValues.bind(crypto)),
      !He)
    )
      throw new Error(
        "crypto.getRandomValues() not supported. See https://github.com/uuidjs/uuid#getrandomvalues-not-supported"
      );
    return He(Ro);
  }
  const $ = [];
  for (let t = 0; t < 256; ++t) $.push((t + 256).toString(16).slice(1));
  function Do(t, e = 0) {
    return (
      $[t[e + 0]] +
      $[t[e + 1]] +
      $[t[e + 2]] +
      $[t[e + 3]] +
      "-" +
      $[t[e + 4]] +
      $[t[e + 5]] +
      "-" +
      $[t[e + 6]] +
      $[t[e + 7]] +
      "-" +
      $[t[e + 8]] +
      $[t[e + 9]] +
      "-" +
      $[t[e + 10]] +
      $[t[e + 11]] +
      $[t[e + 12]] +
      $[t[e + 13]] +
      $[t[e + 14]] +
      $[t[e + 15]]
    ).toLowerCase();
  }
  var vn = {
    randomUUID:
      typeof crypto < "u" &&
      crypto.randomUUID &&
      crypto.randomUUID.bind(crypto),
  };
  function Uo(t, e, n) {
    if (vn.randomUUID && !e && !t) return vn.randomUUID();
    t = t || {};
    const i = t.random || (t.rng || Vo)();
    if (((i[6] = (i[6] & 15) | 64), (i[8] = (i[8] & 63) | 128), e)) {
      n = n || 0;
      for (let s = 0; s < 16; ++s) e[n + s] = i[s];
      return e;
    }
    return Do(i);
  }
  /*! typescript-cookie v1.0.6 | MIT */ const hn = (t) =>
      encodeURIComponent(t)
        .replace(/%(2[346B]|5E|60|7C)/g, decodeURIComponent)
        .replace(/[()]/g, escape),
    bn = (t) =>
      encodeURIComponent(t).replace(
        /%(2[346BF]|3[AC-F]|40|5[BDE]|60|7[BCD])/g,
        decodeURIComponent
      ),
    ht = decodeURIComponent,
    bt = (t) => (
      t[0] === '"' && (t = t.slice(1, -1)),
      t.replace(/(%[\dA-F]{2})+/gi, decodeURIComponent)
    );
  function Mo(t) {
    return (
      (t = Object.assign({}, t)),
      typeof t.expires == "number" &&
        (t.expires = new Date(Date.now() + t.expires * 864e5)),
      t.expires != null && (t.expires = t.expires.toUTCString()),
      Object.entries(t)
        .filter(([e, n]) => n != null && n !== !1)
        .map(([e, n]) => (n === !0 ? `; ${e}` : `; ${e}=${n.split(";")[0]}`))
        .join("")
    );
  }
  function _n(t, e, n) {
    const i = /(?:^|; )([^=]*)=([^;]*)/g,
      s = {};
    let o;
    for (; (o = i.exec(document.cookie)) != null; )
      try {
        const d = n(o[1]);
        if (((s[d] = e(o[2], d)), t === d)) break;
      } catch {}
    return t != null ? s[t] : s;
  }
  const mn = Object.freeze({
      decodeName: ht,
      decodeValue: bt,
      encodeName: hn,
      encodeValue: bn,
    }),
    _t = Object.freeze({ path: "/" });
  function mt(t, e, n = _t, { encodeValue: i = bn, encodeName: s = hn } = {}) {
    return (document.cookie = `${s(t)}=${i(e, t)}${Mo(n)}`);
  }
  function yn(t, { decodeValue: e = bt, decodeName: n = ht } = {}) {
    return _n(t, e, n);
  }
  function jo({ decodeValue: t = bt, decodeName: e = ht } = {}) {
    return _n(void 0, t, e);
  }
  function wn(t, e = _t) {
    mt(t, "", Object.assign({}, e, { expires: -1 }));
  }
  function yt(t, e) {
    const n = {
        set: function (s, o, d) {
          return mt(s, o, Object.assign({}, this.attributes, d), {
            encodeValue: this.converter.write,
          });
        },
        get: function (s) {
          if (arguments.length === 0) return jo(this.converter.read);
          if (s != null) return yn(s, this.converter.read);
        },
        remove: function (s, o) {
          wn(s, Object.assign({}, this.attributes, o));
        },
        withAttributes: function (s) {
          return yt(this.converter, Object.assign({}, this.attributes, s));
        },
        withConverter: function (s) {
          return yt(Object.assign({}, this.converter, s), this.attributes);
        },
      },
      i = {
        attributes: { value: Object.freeze(e) },
        converter: { value: Object.freeze(t) },
      };
    return Object.create(n, i);
  }
  yt({ read: mn.decodeValue, write: mn.encodeValue }, _t);
  class ze {
    constructor(e, n) {
      (this.notice = e), (this.consentPreference = n);
    }
  }
  (y.TCMobileDataVals = void 0),
    ((t) => {
      ((e) => ((e[(e._0 = 0)] = "_0"), (e[(e._1 = 1)] = "_1")))(
        t.IABTCFgdprApplies || (t.IABTCFgdprApplies = {})
      ),
        ((e) => ((e[(e._0 = 0)] = "_0"), (e[(e._1 = 1)] = "_1")))(
          t.IABTCFPurposeOneTreatment || (t.IABTCFPurposeOneTreatment = {})
        ),
        ((e) => ((e[(e._0 = 0)] = "_0"), (e[(e._1 = 1)] = "_1")))(
          t.IABTCFUseNonStandardTexts || (t.IABTCFUseNonStandardTexts = {})
        );
    })(y.TCMobileDataVals || (y.TCMobileDataVals = {}));
  var Cn = ((t) => (
      (t.FRONTEND = "frontend"),
      (t.SYSTEM_WIDE = "system_wide"),
      (t.NOT_APPLICABLE = "not_applicable"),
      t
    ))(Cn || {}),
    z = ((t) => (
      (t.OPT_IN = "opt_in"),
      (t.OPT_OUT = "opt_out"),
      (t.NOTICE_ONLY = "notice_only"),
      t
    ))(z || {}),
    Q = ((t) => (
      (t.OPT_IN = "opt_in"),
      (t.OPT_OUT = "opt_out"),
      (t.ACKNOWLEDGE = "acknowledge"),
      t
    ))(Q || {}),
    ne = ((t) => (
      (t.OVERLAY = "overlay"),
      (t.PRIVACY_CENTER = "privacy_center"),
      (t.TCF_OVERLAY = "tcf_overlay"),
      t
    ))(ne || {}),
    En = ((t) => (
      (t.ALWAYS_ENABLED = "always_enabled"),
      (t.ENABLED_WHERE_REQUIRED = "enabled_where_required"),
      (t.ALWAYS_DISABLED = "always_disabled"),
      t
    ))(En || {}),
    J = ((t) => (
      (t.PRIMARY = "primary"),
      (t.SECONDARY = "secondary"),
      (t.TERTIARY = "tertiary"),
      t
    ))(J || {}),
    G = ((t) => (
      (t.BUTTON = "button"),
      (t.REJECT = "reject"),
      (t.ACCEPT = "accept"),
      (t.SAVE = "save"),
      (t.DISMISS = "dismiss"),
      (t.GPC = "gpc"),
      (t.INDIVIDUAL_NOTICE = "individual_notice"),
      t
    ))(G || {}),
    In = ((t) => (
      (t.privacy_center = "privacy_center"),
      (t.overlay = "overlay"),
      (t.api = "api"),
      t
    ))(In || {}),
    me = ((t) => (
      (t.NONE = "none"),
      (t.APPLIED = "applied"),
      (t.OVERRIDDEN = "overridden"),
      t
    ))(me || {}),
    ue = ((t) => (
      (t.OVERLAY = "overlay"),
      (t.BANNER = "banner"),
      (t.PRIVACY_CENTER = "privacy_center"),
      (t.TCF_OVERLAY = "tcf_overlay"),
      (t.TCF_BANNER = "tcf_banner"),
      t
    ))(ue || {});
  const Ge = (t, e) => !!Object.hasOwn(e.consent, t.notice_key),
    ye = (t) =>
      !t || t === Q.OPT_OUT ? !1 : t === Q.OPT_IN ? !0 : t === Q.ACKNOWLEDGE,
    de = (t, e) =>
      t ? (e === z.NOTICE_ONLY ? Q.ACKNOWLEDGE : Q.OPT_IN) : Q.OPT_OUT,
    xn = (t, e) =>
      t === void 0
        ? !1
        : typeof t == "boolean"
        ? t
        : e.globalPrivacyControl === !0
        ? t.globalPrivacyControl
        : t.value,
    wt = (t, e, n) =>
      t.consent_mechanism === z.NOTICE_ONLY
        ? !0
        : Ge(t, n)
        ? !!n.consent[t.notice_key]
        : ye(t.default_preference),
    Bo = /^\w{2,3}(-\w{2,3})?$/,
    Ho = [
      {
        fidesOption: "fidesEmbed",
        fidesOptionType: "boolean",
        fidesOverrideKey: "fides_embed",
        validationRegex: /^(true|false)$/,
      },
      {
        fidesOption: "fidesDisableSaveApi",
        fidesOptionType: "boolean",
        fidesOverrideKey: "fides_disable_save_api",
        validationRegex: /^(true|false)$/,
      },
      {
        fidesOption: "fidesDisableBanner",
        fidesOptionType: "boolean",
        fidesOverrideKey: "fides_disable_banner",
        validationRegex: /^(true|false)$/,
      },
      {
        fidesOption: "fidesString",
        fidesOptionType: "string",
        fidesOverrideKey: "fides_string",
        validationRegex: /(.*)/,
      },
      {
        fidesOption: "fidesTcfGdprApplies",
        fidesOptionType: "boolean",
        fidesOverrideKey: "fides_tcf_gdpr_applies",
        validationRegex: /^(true|false)$/,
      },
    ],
    b = (t, ...e) => {
      t && console.log(...e);
    },
    we = (t) =>
      !t || typeof t != "object"
        ? !1
        : Object.keys(t).length === 0 || "id" in t,
    Ct = (t, e = !1) => (
      b(e, "constructing geolocation..."),
      t
        ? t.location && Bo.test(t.location)
          ? t.location.replace("-", "_").toLowerCase()
          : t.country && t.region
          ? `${t.country.toLowerCase()}_${t.region.toLowerCase()}`
          : (b(
              e,
              "cannot construct user location from provided geoLocation params..."
            ),
            null)
        : (b(
            e,
            "cannot construct user location since geoLocation is undefined or null"
          ),
          null)
    ),
    On = (t) => {
      if (
        (b(t.debug, "Validating Fides consent overlay options...", t),
        typeof t != "object")
      )
        return !1;
      if (!t.fidesApiUrl)
        return b(t.debug, "Invalid options: fidesApiUrl is required!"), !1;
      if (!t.privacyCenterUrl)
        return b(t.debug, "Invalid options: privacyCenterUrl is required!"), !1;
      try {
        new URL(t.privacyCenterUrl), new URL(t.fidesApiUrl);
      } catch {
        return (
          b(
            t.debug,
            "Invalid options: privacyCenterUrl or fidesApiUrl is an invalid URL!",
            t.privacyCenterUrl
          ),
          !1
        );
      }
      return !0;
    },
    Sn = (t, e) =>
      we(t)
        ? t.component !== ne.OVERLAY && t.component !== ne.TCF_OVERLAY
          ? (b(
              e.debug,
              "No experience found with overlay component. Skipping overlay initialization."
            ),
            !1)
          : t.component === ne.OVERLAY &&
            !(t.privacy_notices && t.privacy_notices.length > 0)
          ? (b(
              e.debug,
              "Privacy experience has no notices. Skipping overlay initialization."
            ),
            !1)
          : t.experience_config
          ? !0
          : (b(
              e.debug,
              "No experience config found with for experience. Skipping overlay initialization."
            ),
            !1)
        : (b(
            e.debug,
            "No relevant experience found. Skipping overlay initialization."
          ),
          !1),
    zo = (t) => {
      var e;
      return (e = t.default_preference) != null ? e : Q.OPT_OUT;
    },
    Pn = (t, e) => {
      var n, i;
      return t.component === ne.TCF_OVERLAY
        ? (n = t.meta) != null && n.version_hash
          ? t.meta.version_hash !== e.tcf_version_hash
          : !0
        : t?.privacy_notices == null || t.privacy_notices.length === 0
        ? !1
        : !((i = t.privacy_notices) != null && i.every((s) => Ge(s, e)));
    },
    Tn = (t) => {
      t[0] === "window" && t.shift();
      let e = window;
      for (; t.length > 0; ) {
        const n = t.shift();
        if (typeof n > "u" || typeof e[n] != "object") return;
        e = e[n];
      }
      return e;
    },
    kn = ({ value: t, notice: e, consentContext: n }) =>
      !n.globalPrivacyControl ||
      !e.has_gpc_flag ||
      e.consent_mechanism === z.NOTICE_ONLY
        ? me.NONE
        : t
        ? me.OVERRIDDEN
        : me.APPLIED;
  var Go = Object.defineProperty,
    Ko = Object.defineProperties,
    Yo = Object.getOwnPropertyDescriptors,
    An = Object.getOwnPropertySymbols,
    qo = Object.prototype.hasOwnProperty,
    Wo = Object.prototype.propertyIsEnumerable,
    Ln = (t, e, n) =>
      e in t
        ? Go(t, e, { enumerable: !0, configurable: !0, writable: !0, value: n })
        : (t[e] = n),
    Ce = (t, e) => {
      for (var n in e || (e = {})) qo.call(e, n) && Ln(t, n, e[n]);
      if (An) for (var n of An(e)) Wo.call(e, n) && Ln(t, n, e[n]);
      return t;
    },
    Ke = (t, e) => Ko(t, Yo(e)),
    Qo = (t, e, n) =>
      new Promise((i, s) => {
        var o = (r) => {
            try {
              a(n.next(r));
            } catch (p) {
              s(p);
            }
          },
          d = (r) => {
            try {
              a(n.throw(r));
            } catch (p) {
              s(p);
            }
          },
          a = (r) =>
            r.done ? i(r.value) : Promise.resolve(r.value).then(o, d);
        a((n = n.apply(t, e)).next());
      });
  const Et = "fides_consent",
    Nn = 365,
    $n = {
      decodeName: decodeURIComponent,
      decodeValue: decodeURIComponent,
      encodeName: encodeURIComponent,
      encodeValue: encodeURIComponent,
    },
    Fn = (t) => (t ? Object.values(t).some((e) => e !== void 0) : !1),
    Rn = () => Uo(),
    Vn = (t) => {
      var e;
      return !((e = t.fides_meta) != null && e.updatedAt);
    },
    Dn = (t) => {
      const e = new Date(),
        n = Rn();
      return {
        consent: t || {},
        identity: { fides_user_device_id: n },
        fides_meta: {
          version: "0.9.0",
          createdAt: e.toISOString(),
          updatedAt: "",
        },
        tcf_consent: {},
      };
    },
    It = (t) => yn(t, $n),
    Un = (t, e = !1) => {
      const n = Dn(t);
      if (typeof document > "u") return n;
      const i = It(Et);
      if (!i)
        return (
          b(
            e,
            "No existing Fides consent cookie found, returning defaults.",
            i
          ),
          n
        );
      try {
        let s;
        const o = JSON.parse(i);
        "consent" in o && "fides_meta" in o
          ? (s = o)
          : (s = Ke(Ce({}, n), { consent: o }));
        const d = Ce(Ce({}, t), s.consent);
        return (
          (s.consent = d),
          b(
            e,
            "Applied existing consent to data from existing Fides consent cookie.",
            JSON.stringify(s)
          ),
          s
        );
      } catch (s) {
        return b(e, "Unable to read consent cookie: invalid JSON.", s), n;
      }
    },
    Mn = (t) => {
      if (typeof document > "u") return;
      const e = new Date().toISOString();
      t.fides_meta.updatedAt = e;
      const n = window.location.hostname.split(".").slice(-2).join(".");
      mt(Et, JSON.stringify(t), { path: "/", domain: n, expires: Nn }, $n);
    },
    xt = ({ experience: t, cookie: e, debug: n }) => {
      var i;
      const s =
        (i = t.privacy_notices) == null
          ? void 0
          : i.map((o) => {
              const d = Object.hasOwn(e.consent, o.notice_key)
                ? de(!!e.consent[o.notice_key], o.consent_mechanism)
                : void 0;
              return Ke(Ce({}, o), { current_preference: d });
            });
      return (
        n &&
          b(
            n,
            "Returning updated pre-fetched experience with user consent.",
            t
          ),
        Ke(Ce({}, t), { privacy_notices: s })
      );
    },
    jn = (t) => {
      const e = {};
      return (
        cn.forEach(({ cookieKey: n }) => {
          var i;
          const s = (i = t[n]) != null ? i : [];
          e[n] = Object.fromEntries(s.map((o) => [o.id, ye(o.preference)]));
        }),
        e
      );
    },
    Bn = (t, e, n) => {
      const i = {};
      return (
        t?.options.forEach(({ cookieKeys: s, default: o }) => {
          if (o === void 0) return;
          const d = xn(o, e);
          s.forEach((a) => {
            const r = i[a];
            if (r === void 0) {
              i[a] = d;
              return;
            }
            i[a] = r && d;
          });
        }),
        b(n, "Returning defaults for legacy config.", i),
        i
      );
    },
    Hn = (t) => {
      t.forEach((e) => {
        var n;
        wn(e.name, { path: (n = e.path) != null ? n : "/", domain: e.domain });
      });
    },
    Ot = (t, e) =>
      Qo(void 0, null, function* () {
        const n = new Map(
            e.map(({ notice: s, consentPreference: o }) => [
              s.notice_key,
              ye(o),
            ])
          ),
          i = Object.fromEntries(n);
        return Ke(Ce({}, t), { consent: i });
      });
  var Jo = Object.defineProperty,
    Zo = Object.defineProperties,
    Xo = Object.getOwnPropertyDescriptors,
    zn = Object.getOwnPropertySymbols,
    er = Object.prototype.hasOwnProperty,
    tr = Object.prototype.propertyIsEnumerable,
    Gn = (t, e, n) =>
      e in t
        ? Jo(t, e, { enumerable: !0, configurable: !0, writable: !0, value: n })
        : (t[e] = n),
    Kn = (t, e) => {
      for (var n in e || (e = {})) er.call(e, n) && Gn(t, n, e[n]);
      if (zn) for (var n of zn(e)) tr.call(e, n) && Gn(t, n, e[n]);
      return t;
    },
    Yn = (t, e) => Zo(t, Xo(e)),
    St = (t, e, n) =>
      new Promise((i, s) => {
        var o = (r) => {
            try {
              a(n.next(r));
            } catch (p) {
              s(p);
            }
          },
          d = (r) => {
            try {
              a(n.throw(r));
            } catch (p) {
              s(p);
            }
          },
          a = (r) =>
            r.done ? i(r.value) : Promise.resolve(r.value).then(o, d);
        a((n = n.apply(t, e)).next());
      }),
    nr = ((t) => (
      (t.PRIVACY_EXPERIENCE = "/privacy-experience"),
      (t.PRIVACY_PREFERENCES = "/privacy-preferences"),
      (t.NOTICES_SERVED = "/notices-served"),
      t
    ))(nr || {});
  const ir = (t, e, n, i) =>
      St(void 0, null, function* () {
        var s;
        if (
          (b(n, `Fetching experience in location: ${t}`),
          i != null && i.getPrivacyExperienceFn)
        ) {
          b(n, "Calling custom fetch experience fn");
          try {
            return yield i.getPrivacyExperienceFn(t, null);
          } catch (r) {
            return (
              b(
                n,
                "Error fetching experience from custom API, returning {}. Error: ",
                r
              ),
              {}
            );
          }
        }
        b(n, "Calling Fides GET experience API");
        const o = {
          method: "GET",
          mode: "cors",
          headers: [["Unescape-Safestr", "true"]],
        };
        let d = {
          show_disabled: "false",
          region: t,
          component: ne.OVERLAY,
          has_notices: "true",
          has_config: "true",
          systems_applicable: "true",
          include_gvl: "true",
          include_meta: "true",
        };
        d = new URLSearchParams(d);
        const a = yield fetch(`${e}/privacy-experience?${d}`, o);
        if (!a.ok)
          return (
            b(
              n,
              "Error getting experience from Fides API, returning {}. Response:",
              a
            ),
            {}
          );
        try {
          const r = yield a.json(),
            p = (s = r.items && r.items[0]) != null ? s : {};
          return (
            b(n, "Got experience response from Fides API, returning: ", p), p
          );
        } catch {
          return (
            b(
              n,
              "Error parsing experience response body from Fides API, returning {}. Response:",
              a
            ),
            {}
          );
        }
      }),
    qn = {
      method: "PATCH",
      mode: "cors",
      headers: { "Content-Type": "application/json" },
    },
    sr = (t, e, n, i, s) =>
      St(void 0, null, function* () {
        var o;
        if (
          (b(n.debug, "Saving user consent preference...", e),
          (o = n.apiOptions) != null && o.savePreferencesFn)
        ) {
          b(n.debug, "Calling custom save preferences fn");
          try {
            yield n.apiOptions.savePreferencesFn(
              t,
              i.consent,
              i.fides_string,
              s
            );
          } catch (r) {
            return (
              b(
                n.debug,
                "Error saving preferences to custom API, continuing. Error: ",
                r
              ),
              Promise.reject(r)
            );
          }
          return Promise.resolve();
        }
        b(n.debug, "Calling Fides save preferences API");
        const d = Yn(Kn({}, qn), { body: JSON.stringify(e) }),
          a = yield fetch(`${n.fidesApiUrl}/privacy-preferences`, d);
        return (
          a.ok ||
            b(
              n.debug,
              "Error patching user preference Fides API. Response:",
              a
            ),
          Promise.resolve()
        );
      }),
    or = (t) =>
      St(void 0, [t], function* ({ request: e, options: n }) {
        var i;
        if (
          (b(n.debug, "Saving that notices were served..."),
          (i = n.apiOptions) != null && i.patchNoticesServedFn)
        ) {
          b(n.debug, "Calling custom patch notices served fn");
          try {
            return yield n.apiOptions.patchNoticesServedFn(e);
          } catch (d) {
            return (
              b(
                n.debug,
                "Error patching notices served to custom API, continuing. Error: ",
                d
              ),
              null
            );
          }
        }
        b(n.debug, "Calling Fides patch notices served API");
        const s = Yn(Kn({}, qn), { body: JSON.stringify(e) }),
          o = yield fetch(`${n.fidesApiUrl}/notices-served`, s);
        return o.ok
          ? o.json()
          : (b(n.debug, "Error patching notices served. Response:", o), null);
      });
  var rr = (t, e, n) =>
    new Promise((i, s) => {
      var o = (r) => {
          try {
            a(n.next(r));
          } catch (p) {
            s(p);
          }
        },
        d = (r) => {
          try {
            a(n.throw(r));
          } catch (p) {
            s(p);
          }
        },
        a = (r) => (r.done ? i(r.value) : Promise.resolve(r.value).then(o, d));
      a((n = n.apply(t, e)).next());
    });
  const ar = (t, e, n = !1) =>
    rr(void 0, null, function* () {
      if ((b(n, "Running getLocation..."), !t))
        return (
          b(
            n,
            "User location could not be retrieved because geolocation is disabled."
          ),
          null
        );
      if (!e)
        return (
          b(
            n,
            "Location cannot be found due to no configured geoLocationApiUrl."
          ),
          null
        );
      b(n, `Calling geolocation API: GET ${e}...`);
      const i = yield fetch(e, { mode: "cors" });
      if (!i.ok)
        return (
          b(
            n,
            "Error getting location from geolocation API, returning {}. Response:",
            i
          ),
          null
        );
      try {
        const s = yield i.json();
        return (
          b(n, "Got location response from geolocation API, returning:", s), s
        );
      } catch {
        return (
          b(
            n,
            "Error parsing response body from geolocation API, returning {}. Response:",
            i
          ),
          null
        );
      }
    });
  var dr = Object.defineProperty,
    lr = Object.defineProperties,
    cr = Object.getOwnPropertyDescriptors,
    Wn = Object.getOwnPropertySymbols,
    pr = Object.prototype.hasOwnProperty,
    ur = Object.prototype.propertyIsEnumerable,
    Qn = (t, e, n) =>
      e in t
        ? dr(t, e, { enumerable: !0, configurable: !0, writable: !0, value: n })
        : (t[e] = n),
    fr = (t, e) => {
      for (var n in e || (e = {})) pr.call(e, n) && Qn(t, n, e[n]);
      if (Wn) for (var n of Wn(e)) ur.call(e, n) && Qn(t, n, e[n]);
      return t;
    },
    gr = (t, e) => lr(t, cr(e));
  const U = (t, e, n, i) => {
    if (typeof window < "u" && typeof CustomEvent < "u") {
      const s = new CustomEvent(t, {
        detail: gr(fr({}, e), { debug: n, extraDetails: i }),
      });
      b(
        n,
        `Dispatching event type ${t} ${
          i != null && i.servingComponent ? `from ${i.servingComponent} ` : ""
        }with cookie ${JSON.stringify(e)} ${
          i != null && i.consentMethod
            ? `using consent method ${i.consentMethod} `
            : ""
        }`
      ),
        window.dispatchEvent(s);
    }
  };
  var vr = Object.defineProperty,
    Jn = Object.getOwnPropertySymbols,
    hr = Object.prototype.hasOwnProperty,
    br = Object.prototype.propertyIsEnumerable,
    Zn = (t, e, n) =>
      e in t
        ? vr(t, e, { enumerable: !0, configurable: !0, writable: !0, value: n })
        : (t[e] = n),
    _r = (t, e) => {
      for (var n in e || (e = {})) hr.call(e, n) && Zn(t, n, e[n]);
      if (Jn) for (var n of Jn(e)) br.call(e, n) && Zn(t, n, e[n]);
      return t;
    },
    Xn = (t, e, n) =>
      new Promise((i, s) => {
        var o = (r) => {
            try {
              a(n.next(r));
            } catch (p) {
              s(p);
            }
          },
          d = (r) => {
            try {
              a(n.throw(r));
            } catch (p) {
              s(p);
            }
          },
          a = (r) =>
            r.done ? i(r.value) : Promise.resolve(r.value).then(o, d);
        a((n = n.apply(t, e)).next());
      });
  function mr(t, e, n, i, s, o, d, a) {
    return Xn(this, null, function* () {
      b(t.debug, "Saving preferences to Fides API");
      const r = s?.map((l) => ({
          privacy_notice_history_id: l.notice.privacy_notice_history_id,
          preference: l.consentPreference,
        })),
        p = _r(
          {
            browser_identity: e.identity,
            preferences: r,
            privacy_experience_id: n.id,
            user_geography: d,
            method: i,
            served_notice_history_id: a,
          },
          o ?? []
        );
      yield sr(i, p, t, e, n);
    });
  }
  const Pt = (t) =>
    Xn(
      void 0,
      [t],
      function* ({
        consentPreferencesToSave: e,
        experience: n,
        consentMethod: i,
        options: s,
        userLocationString: o,
        cookie: d,
        servedNoticeHistoryId: a,
        tcf: r,
        updateCookie: p,
      }) {
        if (s.fidesPreviewMode) return;
        const l = { consentMethod: i },
          f = yield p(d);
        if (
          (Object.assign(d, f),
          Object.assign(d.fides_meta, l),
          b(s.debug, "Updating window.Fides"),
          (window.Fides.consent = d.consent),
          (window.Fides.fides_string = d.fides_string),
          (window.Fides.tcf_consent = d.tcf_consent),
          !s.fidesDisableSaveApi)
        )
          try {
            yield mr(s, d, n, i, e, r, o, a);
          } catch (u) {
            b(
              s.debug,
              "Error saving updated preferences to API, continuing. Error: ",
              u
            );
          }
        b(s.debug, "Saving preferences to cookie"),
          Mn(d),
          e &&
            e
              .filter((u) => u.consentPreference === Q.OPT_OUT)
              .forEach((u) => {
                Hn(u.notice.cookies);
              }),
          U("FidesUpdated", d, s.debug, l);
      }
    );
  var Tt = (t, e, n) =>
    new Promise((i, s) => {
      var o = (r) => {
          try {
            a(n.next(r));
          } catch (p) {
            s(p);
          }
        },
        d = (r) => {
          try {
            a(n.throw(r));
          } catch (p) {
            s(p);
          }
        },
        a = (r) => (r.done ? i(r.value) : Promise.resolve(r.value).then(o, d));
      a((n = n.apply(t, e)).next());
    });
  const yr = "fides-embed-container",
    wr = "fides-overlay",
    ei = (t) =>
      Tt(
        void 0,
        [t],
        function* ({
          experience: e,
          fidesRegionString: n,
          cookie: i,
          options: s,
          renderOverlay: o,
        }) {
          b(s.debug, "Initializing Fides consent overlays...");
          function d() {
            return Tt(this, null, function* () {
              try {
                b(
                  s.debug,
                  "Rendering Fides overlay CSS & HTML into the DOM..."
                );
                let a;
                if (s.fidesEmbed) {
                  if (((a = document.getElementById(yr)), !a))
                    throw new Error(
                      "Element with id fides-embed-container could not be found."
                    );
                } else {
                  const r = s.overlayParentId || wr;
                  (a = document.getElementById(r)),
                    a ||
                      (b(
                        s.debug,
                        `Parent element not found (#${r}), creating and appending to body...`
                      ),
                      (a = document.createElement("div")),
                      (a.id = r),
                      document.body.prepend(a));
                }
                return (
                  (e.component === ne.OVERLAY ||
                    e.component === ne.TCF_OVERLAY) &&
                    (o(
                      {
                        experience: e,
                        fidesRegionString: n,
                        cookie: i,
                        options: s,
                      },
                      a
                    ),
                    b(s.debug, "Fides overlay is now showing!")),
                  yield Promise.resolve()
                );
              } catch (a) {
                return b(s.debug, a), Promise.reject(a);
              }
            });
          }
          return (
            document?.readyState !== "complete"
              ? (b(s.debug, "DOM not loaded, adding event listener"),
                document.addEventListener("readystatechange", () =>
                  Tt(void 0, null, function* () {
                    document.readyState === "complete" &&
                      (b(s.debug, "DOM fully loaded and parsed"), yield d());
                  })
                ))
              : yield d(),
            Promise.resolve()
          );
        }
      );
  var Cr = (t, e, n) =>
    new Promise((i, s) => {
      var o = (r) => {
          try {
            a(n.next(r));
          } catch (p) {
            s(p);
          }
        },
        d = (r) => {
          try {
            a(n.throw(r));
          } catch (p) {
            s(p);
          }
        },
        a = (r) => (r.done ? i(r.value) : Promise.resolve(r.value).then(o, d));
      a((n = n.apply(t, e)).next());
    });
  const Er = (t) =>
    Cr(void 0, [t], function* ({ options: e, experience: n }) {
      var i;
      if ((i = n?.gpp_settings) != null && i.enabled)
        try {
          yield import(`${e.fidesJsBaseUrl}/fides-ext-gpp.js`);
        } catch (s) {
          console.error("Unable to import GPP extension", s);
        }
    });
  var ti = (t, e, n) =>
    new Promise((i, s) => {
      var o = (r) => {
          try {
            a(n.next(r));
          } catch (p) {
            s(p);
          }
        },
        d = (r) => {
          try {
            a(n.throw(r));
          } catch (p) {
            s(p);
          }
        },
        a = (r) => (r.done ? i(r.value) : Promise.resolve(r.value).then(o, d));
      a((n = n.apply(t, e)).next());
    });
  const Ir = (t, e) =>
      ti(void 0, null, function* () {
        return (
          Ct(t) ||
          Ct(yield ar(e.isGeolocationEnabled, e.geolocationApiUrl, e.debug))
        );
      }),
    xr = ({
      cookie: t,
      fidesRegionString: e,
      effectiveExperience: n,
      fidesOptions: i,
    }) => {
      if (!n || !n.privacy_notices) return !1;
      const s = ae();
      if (!s.globalPrivacyControl) return !1;
      let o = !1;
      const d = n.privacy_notices.map((a) => {
        const r = Ge(a, t);
        return a.has_gpc_flag && !r && a.consent_mechanism !== z.NOTICE_ONLY
          ? ((o = !0), new ze(a, de(!1, a.consent_mechanism)))
          : new ze(a, de(wt(a, s, t), a.consent_mechanism));
      });
      return o
        ? (Pt({
            consentPreferencesToSave: d,
            experience: n,
            consentMethod: G.GPC,
            options: i,
            userLocationString: e || void 0,
            cookie: t,
            updateCookie: (a) => Ot(a, d),
          }),
          !0)
        : !1;
    },
    ni = (t) => {
      const e = {};
      if (typeof window < "u") {
        const n = new URLSearchParams(window.location.search),
          i =
            t.options.customOptionsPath &&
            t.options.customOptionsPath.split("."),
          s = i && i.length >= 0 ? Tn(i) : window.fides_overrides;
        Ho.forEach(
          ({
            fidesOption: o,
            fidesOptionType: d,
            fidesOverrideKey: a,
            validationRegex: r,
          }) => {
            const p = n.get(a),
              l = s ? s[a] : void 0,
              f = It(a),
              u = p || l || f;
            u &&
              r.test(u.toString()) &&
              (e[o] = d === "string" ? u : JSON.parse(u.toString()));
          }
        );
      }
      return e;
    },
    ii = ({ consent: t, options: e }) => {
      const n = ae(),
        i = Bn(t, n, e.debug);
      return Un(i, e.debug);
    },
    si = ({
      cookie: t,
      experience: e,
      geolocation: n,
      options: i,
      updateExperienceFromCookieConsent: s,
    }) => {
      if (Vn(t) && !i.fidesString) return null;
      let o = e;
      return (
        we(e) && (o = s({ experience: e, cookie: t, debug: i.debug })),
        {
          consent: t.consent,
          fides_meta: t.fides_meta,
          identity: t.identity,
          experience: o,
          tcf_consent: t.tcf_consent,
          fides_string: t.fides_string,
          geolocation: n,
          options: i,
          initialized: !0,
        }
      );
    },
    oi = (t) =>
      ti(
        void 0,
        [t],
        function* ({
          cookie: e,
          options: n,
          experience: i,
          geolocation: s,
          renderOverlay: o,
          updateExperience: d,
        }) {
          let a = n.isOverlayEnabled,
            r = i,
            p = null;
          if (a) {
            On(n) ||
              (b(
                n.debug,
                "Invalid overlay options. Skipping overlay initialization.",
                n
              ),
              (a = !1)),
              (p = yield Ir(s, n));
            let l = !1;
            if (
              (p
                ? we(r) ||
                  ((l = !0),
                  (r = yield ir(p, n.fidesApiUrl, n.debug, n.apiOptions)))
                : (b(
                    n.debug,
                    "User location could not be obtained. Skipping overlay initialization."
                  ),
                  (a = !1)),
              we(r) && Sn(r, n))
            ) {
              a &&
                we(r) &&
                xr({
                  cookie: e,
                  fidesRegionString: p,
                  effectiveExperience: r,
                  fidesOptions: n,
                });
              const f = yield d({
                cookie: e,
                experience: r,
                debug: n.debug,
                isExperienceClientSideFetched: l,
              });
              b(n.debug, "Updated experience", f),
                Object.assign(r, f),
                a &&
                  (yield ei({
                    experience: r,
                    fidesRegionString: p,
                    cookie: e,
                    options: n,
                    renderOverlay: o,
                  }).catch(() => {}));
            }
          }
          return (
            yield Er({ options: n, experience: r }),
            {
              consent: e.consent,
              fides_meta: e.fides_meta,
              identity: e.identity,
              fides_string: e.fides_string,
              tcf_consent: e.tcf_consent,
              experience: r,
              geolocation: s,
              options: n,
              initialized: !0,
            }
          );
        }
      );
  var Ye,
    E,
    ri,
    fe,
    ai,
    di,
    kt,
    qe = {},
    li = [],
    Or = /acit|ex(?:s|g|n|p|$)|rph|grid|ows|mnc|ntw|ine[ch]|zoo|^ord|itera/i,
    At = Array.isArray;
  function le(t, e) {
    for (var n in e) t[n] = e[n];
    return t;
  }
  function ci(t) {
    var e = t.parentNode;
    e && e.removeChild(t);
  }
  function c(t, e, n) {
    var i,
      s,
      o,
      d = {};
    for (o in e)
      o == "key" ? (i = e[o]) : o == "ref" ? (s = e[o]) : (d[o] = e[o]);
    if (
      (arguments.length > 2 &&
        (d.children = arguments.length > 3 ? Ye.call(arguments, 2) : n),
      typeof t == "function" && t.defaultProps != null)
    )
      for (o in t.defaultProps) d[o] === void 0 && (d[o] = t.defaultProps[o]);
    return We(t, d, i, s, null);
  }
  function We(t, e, n, i, s) {
    var o = {
      type: t,
      props: e,
      key: n,
      ref: i,
      __k: null,
      __: null,
      __b: 0,
      __e: null,
      __d: void 0,
      __c: null,
      __h: null,
      constructor: void 0,
      __v: s ?? ++ri,
    };
    return s == null && E.vnode != null && E.vnode(o), o;
  }
  function K(t) {
    return t.children;
  }
  function Qe(t, e) {
    (this.props = t), (this.context = e);
  }
  function Ne(t, e) {
    if (e == null) return t.__ ? Ne(t.__, t.__.__k.indexOf(t) + 1) : null;
    for (var n; e < t.__k.length; e++)
      if ((n = t.__k[e]) != null && n.__e != null) return n.__e;
    return typeof t.type == "function" ? Ne(t) : null;
  }
  function pi(t) {
    var e, n;
    if ((t = t.__) != null && t.__c != null) {
      for (t.__e = t.__c.base = null, e = 0; e < t.__k.length; e++)
        if ((n = t.__k[e]) != null && n.__e != null) {
          t.__e = t.__c.base = n.__e;
          break;
        }
      return pi(t);
    }
  }
  function ui(t) {
    ((!t.__d && (t.__d = !0) && fe.push(t) && !Je.__r++) ||
      ai !== E.debounceRendering) &&
      ((ai = E.debounceRendering) || di)(Je);
  }
  function Je() {
    var t, e, n, i, s, o, d, a;
    for (fe.sort(kt); (t = fe.shift()); )
      t.__d &&
        ((e = fe.length),
        (i = void 0),
        (s = void 0),
        (d = (o = (n = t).__v).__e),
        (a = n.__P) &&
          ((i = []),
          ((s = le({}, o)).__v = o.__v + 1),
          Lt(
            a,
            o,
            s,
            n.__n,
            a.ownerSVGElement !== void 0,
            o.__h != null ? [d] : null,
            i,
            d ?? Ne(o),
            o.__h
          ),
          yi(i, o),
          o.__e != d && pi(o)),
        fe.length > e && fe.sort(kt));
    Je.__r = 0;
  }
  function fi(t, e, n, i, s, o, d, a, r, p) {
    var l,
      f,
      u,
      g,
      h,
      T,
      m,
      C = (i && i.__k) || li,
      O = C.length;
    for (n.__k = [], l = 0; l < e.length; l++)
      if (
        (g = n.__k[l] =
          (g = e[l]) == null || typeof g == "boolean" || typeof g == "function"
            ? null
            : typeof g == "string" ||
              typeof g == "number" ||
              typeof g == "bigint"
            ? We(null, g, null, null, g)
            : At(g)
            ? We(K, { children: g }, null, null, null)
            : g.__b > 0
            ? We(g.type, g.props, g.key, g.ref ? g.ref : null, g.__v)
            : g) != null
      ) {
        if (
          ((g.__ = n),
          (g.__b = n.__b + 1),
          (u = C[l]) === null || (u && g.key == u.key && g.type === u.type))
        )
          C[l] = void 0;
        else
          for (f = 0; f < O; f++) {
            if ((u = C[f]) && g.key == u.key && g.type === u.type) {
              C[f] = void 0;
              break;
            }
            u = null;
          }
        Lt(t, g, (u = u || qe), s, o, d, a, r, p),
          (h = g.__e),
          (f = g.ref) &&
            u.ref != f &&
            (m || (m = []),
            u.ref && m.push(u.ref, null, g),
            m.push(f, g.__c || h, g)),
          h != null
            ? (T == null && (T = h),
              typeof g.type == "function" && g.__k === u.__k
                ? (g.__d = r = gi(g, r, t))
                : (r = vi(t, g, u, C, h, r)),
              typeof n.type == "function" && (n.__d = r))
            : r && u.__e == r && r.parentNode != t && (r = Ne(u));
      }
    for (n.__e = T, l = O; l--; )
      C[l] != null &&
        (typeof n.type == "function" &&
          C[l].__e != null &&
          C[l].__e == n.__d &&
          (n.__d = hi(i).nextSibling),
        Ci(C[l], C[l]));
    if (m) for (l = 0; l < m.length; l++) wi(m[l], m[++l], m[++l]);
  }
  function gi(t, e, n) {
    for (var i, s = t.__k, o = 0; s && o < s.length; o++)
      (i = s[o]) &&
        ((i.__ = t),
        (e =
          typeof i.type == "function"
            ? gi(i, e, n)
            : vi(n, i, i, s, i.__e, e)));
    return e;
  }
  function vi(t, e, n, i, s, o) {
    var d, a, r;
    if (e.__d !== void 0) (d = e.__d), (e.__d = void 0);
    else if (n == null || s != o || s.parentNode == null)
      e: if (o == null || o.parentNode !== t) t.appendChild(s), (d = null);
      else {
        for (a = o, r = 0; (a = a.nextSibling) && r < i.length; r += 1)
          if (a == s) break e;
        t.insertBefore(s, o), (d = o);
      }
    return d !== void 0 ? d : s.nextSibling;
  }
  function hi(t) {
    var e, n, i;
    if (t.type == null || typeof t.type == "string") return t.__e;
    if (t.__k) {
      for (e = t.__k.length - 1; e >= 0; e--)
        if ((n = t.__k[e]) && (i = hi(n))) return i;
    }
    return null;
  }
  function Sr(t, e, n, i, s) {
    var o;
    for (o in n)
      o === "children" || o === "key" || o in e || Ze(t, o, null, n[o], i);
    for (o in e)
      (s && typeof e[o] != "function") ||
        o === "children" ||
        o === "key" ||
        o === "value" ||
        o === "checked" ||
        n[o] === e[o] ||
        Ze(t, o, e[o], n[o], i);
  }
  function bi(t, e, n) {
    e[0] === "-"
      ? t.setProperty(e, n ?? "")
      : (t[e] =
          n == null ? "" : typeof n != "number" || Or.test(e) ? n : n + "px");
  }
  function Ze(t, e, n, i, s) {
    var o;
    e: if (e === "style")
      if (typeof n == "string") t.style.cssText = n;
      else {
        if ((typeof i == "string" && (t.style.cssText = i = ""), i))
          for (e in i) (n && e in n) || bi(t.style, e, "");
        if (n) for (e in n) (i && n[e] === i[e]) || bi(t.style, e, n[e]);
      }
    else if (e[0] === "o" && e[1] === "n")
      (o = e !== (e = e.replace(/Capture$/, ""))),
        (e = e.toLowerCase() in t ? e.toLowerCase().slice(2) : e.slice(2)),
        t.l || (t.l = {}),
        (t.l[e + o] = n),
        n
          ? i || t.addEventListener(e, o ? mi : _i, o)
          : t.removeEventListener(e, o ? mi : _i, o);
    else if (e !== "dangerouslySetInnerHTML") {
      if (s) e = e.replace(/xlink(H|:h)/, "h").replace(/sName$/, "s");
      else if (
        e !== "width" &&
        e !== "height" &&
        e !== "href" &&
        e !== "list" &&
        e !== "form" &&
        e !== "tabIndex" &&
        e !== "download" &&
        e !== "rowSpan" &&
        e !== "colSpan" &&
        e in t
      )
        try {
          t[e] = n ?? "";
          break e;
        } catch {}
      typeof n == "function" ||
        (n == null || (n === !1 && e[4] !== "-")
          ? t.removeAttribute(e)
          : t.setAttribute(e, n));
    }
  }
  function _i(t) {
    return this.l[t.type + !1](E.event ? E.event(t) : t);
  }
  function mi(t) {
    return this.l[t.type + !0](E.event ? E.event(t) : t);
  }
  function Lt(t, e, n, i, s, o, d, a, r) {
    var p,
      l,
      f,
      u,
      g,
      h,
      T,
      m,
      C,
      O,
      S,
      k,
      V,
      R,
      B,
      H = e.type;
    if (e.constructor !== void 0) return null;
    n.__h != null &&
      ((r = n.__h), (a = e.__e = n.__e), (e.__h = null), (o = [a])),
      (p = E.__b) && p(e);
    try {
      e: if (typeof H == "function") {
        if (
          ((m = e.props),
          (C = (p = H.contextType) && i[p.__c]),
          (O = p ? (C ? C.props.value : p.__) : i),
          n.__c
            ? (T = (l = e.__c = n.__c).__ = l.__E)
            : ("prototype" in H && H.prototype.render
                ? (e.__c = l = new H(m, O))
                : ((e.__c = l = new Qe(m, O)),
                  (l.constructor = H),
                  (l.render = Tr)),
              C && C.sub(l),
              (l.props = m),
              l.state || (l.state = {}),
              (l.context = O),
              (l.__n = i),
              (f = l.__d = !0),
              (l.__h = []),
              (l._sb = [])),
          l.__s == null && (l.__s = l.state),
          H.getDerivedStateFromProps != null &&
            (l.__s == l.state && (l.__s = le({}, l.__s)),
            le(l.__s, H.getDerivedStateFromProps(m, l.__s))),
          (u = l.props),
          (g = l.state),
          (l.__v = e),
          f)
        )
          H.getDerivedStateFromProps == null &&
            l.componentWillMount != null &&
            l.componentWillMount(),
            l.componentDidMount != null && l.__h.push(l.componentDidMount);
        else {
          if (
            (H.getDerivedStateFromProps == null &&
              m !== u &&
              l.componentWillReceiveProps != null &&
              l.componentWillReceiveProps(m, O),
            (!l.__e &&
              l.shouldComponentUpdate != null &&
              l.shouldComponentUpdate(m, l.__s, O) === !1) ||
              e.__v === n.__v)
          ) {
            for (
              e.__v !== n.__v &&
                ((l.props = m), (l.state = l.__s), (l.__d = !1)),
                l.__e = !1,
                e.__e = n.__e,
                e.__k = n.__k,
                e.__k.forEach(function (lt) {
                  lt && (lt.__ = e);
                }),
                S = 0;
              S < l._sb.length;
              S++
            )
              l.__h.push(l._sb[S]);
            (l._sb = []), l.__h.length && d.push(l);
            break e;
          }
          l.componentWillUpdate != null && l.componentWillUpdate(m, l.__s, O),
            l.componentDidUpdate != null &&
              l.__h.push(function () {
                l.componentDidUpdate(u, g, h);
              });
        }
        if (
          ((l.context = O),
          (l.props = m),
          (l.__P = t),
          (k = E.__r),
          (V = 0),
          "prototype" in H && H.prototype.render)
        ) {
          for (
            l.state = l.__s,
              l.__d = !1,
              k && k(e),
              p = l.render(l.props, l.state, l.context),
              R = 0;
            R < l._sb.length;
            R++
          )
            l.__h.push(l._sb[R]);
          l._sb = [];
        } else
          do
            (l.__d = !1),
              k && k(e),
              (p = l.render(l.props, l.state, l.context)),
              (l.state = l.__s);
          while (l.__d && ++V < 25);
        (l.state = l.__s),
          l.getChildContext != null && (i = le(le({}, i), l.getChildContext())),
          f ||
            l.getSnapshotBeforeUpdate == null ||
            (h = l.getSnapshotBeforeUpdate(u, g)),
          fi(
            t,
            At(
              (B =
                p != null && p.type === K && p.key == null
                  ? p.props.children
                  : p)
            )
              ? B
              : [B],
            e,
            n,
            i,
            s,
            o,
            d,
            a,
            r
          ),
          (l.base = e.__e),
          (e.__h = null),
          l.__h.length && d.push(l),
          T && (l.__E = l.__ = null),
          (l.__e = !1);
      } else o == null && e.__v === n.__v ? ((e.__k = n.__k), (e.__e = n.__e)) : (e.__e = Pr(n.__e, e, n, i, s, o, d, r));
      (p = E.diffed) && p(e);
    } catch (lt) {
      (e.__v = null),
        (r || o != null) &&
          ((e.__e = a), (e.__h = !!r), (o[o.indexOf(a)] = null)),
        E.__e(lt, e, n);
    }
  }
  function yi(t, e) {
    E.__c && E.__c(e, t),
      t.some(function (n) {
        try {
          (t = n.__h),
            (n.__h = []),
            t.some(function (i) {
              i.call(n);
            });
        } catch (i) {
          E.__e(i, n.__v);
        }
      });
  }
  function Pr(t, e, n, i, s, o, d, a) {
    var r,
      p,
      l,
      f = n.props,
      u = e.props,
      g = e.type,
      h = 0;
    if ((g === "svg" && (s = !0), o != null)) {
      for (; h < o.length; h++)
        if (
          (r = o[h]) &&
          "setAttribute" in r == !!g &&
          (g ? r.localName === g : r.nodeType === 3)
        ) {
          (t = r), (o[h] = null);
          break;
        }
    }
    if (t == null) {
      if (g === null) return document.createTextNode(u);
      (t = s
        ? document.createElementNS("http://www.w3.org/2000/svg", g)
        : document.createElement(g, u.is && u)),
        (o = null),
        (a = !1);
    }
    if (g === null) f === u || (a && t.data === u) || (t.data = u);
    else {
      if (
        ((o = o && Ye.call(t.childNodes)),
        (p = (f = n.props || qe).dangerouslySetInnerHTML),
        (l = u.dangerouslySetInnerHTML),
        !a)
      ) {
        if (o != null)
          for (f = {}, h = 0; h < t.attributes.length; h++)
            f[t.attributes[h].name] = t.attributes[h].value;
        (l || p) &&
          ((l && ((p && l.__html == p.__html) || l.__html === t.innerHTML)) ||
            (t.innerHTML = (l && l.__html) || ""));
      }
      if ((Sr(t, u, f, s, a), l)) e.__k = [];
      else if (
        (fi(
          t,
          At((h = e.props.children)) ? h : [h],
          e,
          n,
          i,
          s && g !== "foreignObject",
          o,
          d,
          o ? o[0] : n.__k && Ne(n, 0),
          a
        ),
        o != null)
      )
        for (h = o.length; h--; ) o[h] != null && ci(o[h]);
      a ||
        ("value" in u &&
          (h = u.value) !== void 0 &&
          (h !== t.value ||
            (g === "progress" && !h) ||
            (g === "option" && h !== f.value)) &&
          Ze(t, "value", h, f.value, !1),
        "checked" in u &&
          (h = u.checked) !== void 0 &&
          h !== t.checked &&
          Ze(t, "checked", h, f.checked, !1));
    }
    return t;
  }
  function wi(t, e, n) {
    try {
      typeof t == "function" ? t(e) : (t.current = e);
    } catch (i) {
      E.__e(i, n);
    }
  }
  function Ci(t, e, n) {
    var i, s;
    if (
      (E.unmount && E.unmount(t),
      (i = t.ref) && ((i.current && i.current !== t.__e) || wi(i, null, e)),
      (i = t.__c) != null)
    ) {
      if (i.componentWillUnmount)
        try {
          i.componentWillUnmount();
        } catch (o) {
          E.__e(o, e);
        }
      (i.base = i.__P = null), (t.__c = void 0);
    }
    if ((i = t.__k))
      for (s = 0; s < i.length; s++)
        i[s] && Ci(i[s], e, n || typeof t.type != "function");
    n || t.__e == null || ci(t.__e), (t.__ = t.__e = t.__d = void 0);
  }
  function Tr(t, e, n) {
    return this.constructor(t, n);
  }
  function Ei(t, e, n) {
    var i, s, o;
    E.__ && E.__(t, e),
      (s = (i = typeof n == "function") ? null : (n && n.__k) || e.__k),
      (o = []),
      Lt(
        e,
        (t = ((!i && n) || e).__k = c(K, null, [t])),
        s || qe,
        qe,
        e.ownerSVGElement !== void 0,
        !i && n ? [n] : s ? null : e.firstChild ? Ye.call(e.childNodes) : null,
        o,
        !i && n ? n : s ? s.__e : e.firstChild,
        i
      ),
      yi(o, t);
  }
  (Ye = li.slice),
    (E = {
      __e: function (t, e, n, i) {
        for (var s, o, d; (e = e.__); )
          if ((s = e.__c) && !s.__)
            try {
              if (
                ((o = s.constructor) &&
                  o.getDerivedStateFromError != null &&
                  (s.setState(o.getDerivedStateFromError(t)), (d = s.__d)),
                s.componentDidCatch != null &&
                  (s.componentDidCatch(t, i || {}), (d = s.__d)),
                d)
              )
                return (s.__E = s);
            } catch (a) {
              t = a;
            }
        throw t;
      },
    }),
    (ri = 0),
    (Qe.prototype.setState = function (t, e) {
      var n;
      (n =
        this.__s != null && this.__s !== this.state
          ? this.__s
          : (this.__s = le({}, this.state))),
        typeof t == "function" && (t = t(le({}, n), this.props)),
        t && le(n, t),
        t != null && this.__v && (e && this._sb.push(e), ui(this));
    }),
    (Qe.prototype.forceUpdate = function (t) {
      this.__v && ((this.__e = !0), t && this.__h.push(t), ui(this));
    }),
    (Qe.prototype.render = K),
    (fe = []),
    (di =
      typeof Promise == "function"
        ? Promise.prototype.then.bind(Promise.resolve())
        : setTimeout),
    (kt = function (t, e) {
      return t.__v.__b - e.__v.__b;
    }),
    (Je.__r = 0);
  var $e,
    A,
    Nt,
    Ii,
    Fe = 0,
    xi = [],
    Xe = [],
    Oi = E.__b,
    Si = E.__r,
    Pi = E.diffed,
    Ti = E.__c,
    ki = E.unmount;
  function $t(t, e) {
    E.__h && E.__h(A, t, Fe || e), (Fe = 0);
    var n = A.__H || (A.__H = { __: [], __h: [] });
    return t >= n.__.length && n.__.push({ __V: Xe }), n.__[t];
  }
  function j(t) {
    return (Fe = 1), kr(Ni, t);
  }
  function kr(t, e, n) {
    var i = $t($e++, 2);
    if (
      ((i.t = t),
      !i.__c &&
        ((i.__ = [
          n ? n(e) : Ni(void 0, e),
          function (a) {
            var r = i.__N ? i.__N[0] : i.__[0],
              p = i.t(r, a);
            r !== p && ((i.__N = [p, i.__[1]]), i.__c.setState({}));
          },
        ]),
        (i.__c = A),
        !A.u))
    ) {
      var s = function (a, r, p) {
        if (!i.__c.__H) return !0;
        var l = i.__c.__H.__.filter(function (u) {
          return u.__c;
        });
        if (
          l.every(function (u) {
            return !u.__N;
          })
        )
          return !o || o.call(this, a, r, p);
        var f = !1;
        return (
          l.forEach(function (u) {
            if (u.__N) {
              var g = u.__[0];
              (u.__ = u.__N), (u.__N = void 0), g !== u.__[0] && (f = !0);
            }
          }),
          !(!f && i.__c.props === a) && (!o || o.call(this, a, r, p))
        );
      };
      A.u = !0;
      var o = A.shouldComponentUpdate,
        d = A.componentWillUpdate;
      (A.componentWillUpdate = function (a, r, p) {
        if (this.__e) {
          var l = o;
          (o = void 0), s(a, r, p), (o = l);
        }
        d && d.call(this, a, r, p);
      }),
        (A.shouldComponentUpdate = s);
    }
    return i.__N || i.__;
  }
  function ie(t, e) {
    var n = $t($e++, 3);
    !E.__s && Li(n.__H, e) && ((n.__ = t), (n.i = e), A.__H.__h.push(n));
  }
  function et(t) {
    return (
      (Fe = 5),
      F(function () {
        return { current: t };
      }, [])
    );
  }
  function F(t, e) {
    var n = $t($e++, 7);
    return Li(n.__H, e) ? ((n.__V = t()), (n.i = e), (n.__h = t), n.__V) : n.__;
  }
  function L(t, e) {
    return (
      (Fe = 8),
      F(function () {
        return t;
      }, e)
    );
  }
  function Ar() {
    for (var t; (t = xi.shift()); )
      if (t.__P && t.__H)
        try {
          t.__H.__h.forEach(tt), t.__H.__h.forEach(Ft), (t.__H.__h = []);
        } catch (e) {
          (t.__H.__h = []), E.__e(e, t.__v);
        }
  }
  (E.__b = function (t) {
    (A = null), Oi && Oi(t);
  }),
    (E.__r = function (t) {
      Si && Si(t), ($e = 0);
      var e = (A = t.__c).__H;
      e &&
        (Nt === A
          ? ((e.__h = []),
            (A.__h = []),
            e.__.forEach(function (n) {
              n.__N && (n.__ = n.__N), (n.__V = Xe), (n.__N = n.i = void 0);
            }))
          : (e.__h.forEach(tt), e.__h.forEach(Ft), (e.__h = []), ($e = 0))),
        (Nt = A);
    }),
    (E.diffed = function (t) {
      Pi && Pi(t);
      var e = t.__c;
      e &&
        e.__H &&
        (e.__H.__h.length &&
          ((xi.push(e) !== 1 && Ii === E.requestAnimationFrame) ||
            ((Ii = E.requestAnimationFrame) || Lr)(Ar)),
        e.__H.__.forEach(function (n) {
          n.i && (n.__H = n.i),
            n.__V !== Xe && (n.__ = n.__V),
            (n.i = void 0),
            (n.__V = Xe);
        })),
        (Nt = A = null);
    }),
    (E.__c = function (t, e) {
      e.some(function (n) {
        try {
          n.__h.forEach(tt),
            (n.__h = n.__h.filter(function (i) {
              return !i.__ || Ft(i);
            }));
        } catch (i) {
          e.some(function (s) {
            s.__h && (s.__h = []);
          }),
            (e = []),
            E.__e(i, n.__v);
        }
      }),
        Ti && Ti(t, e);
    }),
    (E.unmount = function (t) {
      ki && ki(t);
      var e,
        n = t.__c;
      n &&
        n.__H &&
        (n.__H.__.forEach(function (i) {
          try {
            tt(i);
          } catch (s) {
            e = s;
          }
        }),
        (n.__H = void 0),
        e && E.__e(e, n.__v));
    });
  var Ai = typeof requestAnimationFrame == "function";
  function Lr(t) {
    var e,
      n = function () {
        clearTimeout(i), Ai && cancelAnimationFrame(e), setTimeout(t);
      },
      i = setTimeout(n, 100);
    Ai && (e = requestAnimationFrame(n));
  }
  function tt(t) {
    var e = A,
      n = t.__c;
    typeof n == "function" && ((t.__c = void 0), n()), (A = e);
  }
  function Ft(t) {
    var e = A;
    (t.__c = t.__()), (A = e);
  }
  function Li(t, e) {
    return (
      !t ||
      t.length !== e.length ||
      e.some(function (n, i) {
        return n !== t[i];
      })
    );
  }
  function Ni(t, e) {
    return typeof e == "function" ? e(t) : e;
  }
  const $i = ({ onClick: t, ariaLabel: e, hidden: n = !1 }) =>
      c(
        "button",
        {
          type: "button",
          "aria-label": e,
          className: "fides-close-button",
          onClick: t,
          style: { visibility: n ? "hidden" : "visible" },
        },
        c(
          "svg",
          {
            xmlns: "http://www.w3.org/2000/svg",
            width: "16",
            height: "16",
            fill: "none",
          },
          c("path", {
            fill: "#2D3748",
            d: "m8 7.057 3.3-3.3.943.943-3.3 3.3 3.3 3.3-.943.943-3.3-3.3-3.3 3.3-.943-.943 3.3-3.3-3.3-3.3.943-.943 3.3 3.3Z",
          })
        )
      ),
    Fi = ({ label: t, status: e }) =>
      c(
        "span",
        { className: "fides-gpc-label" },
        t,
        " ",
        c("span", { className: `fides-gpc-badge fides-gpc-badge-${e}` }, e)
      ),
    Nr = ({ value: t, notice: e }) => {
      const n = ae(),
        i = kn({ value: t, notice: e, consentContext: n });
      return i === me.NONE
        ? null
        : c(Fi, { label: "Global Privacy Control", status: i.valueOf() });
    },
    nt = "vendors page.",
    Ri = ({
      description: t,
      onVendorPageClick: e,
      allowHTMLDescription: n = !1,
    }) => {
      if (!t) return null;
      if (n)
        return c("div", {
          className: "fides-html-description",
          dangerouslySetInnerHTML: { __html: t },
        });
      if (
        e &&
        (t.endsWith(nt) ||
          t.endsWith(`${nt}
`))
      ) {
        const i = t.split(nt)[0];
        return c(
          "div",
          null,
          i,
          " ",
          c(
            "button",
            { type: "button", className: "fides-link-button", onClick: e },
            nt
          )
        );
      }
      return c("div", null, t);
    },
    Rt = ({
      experience: t,
      onOpen: e,
      onClose: n,
      bannerIsOpen: i,
      children: s,
      onVendorPageClick: o,
      renderButtonGroup: d,
      className: a,
      fidesPreviewMode: r,
    }) => {
      var p, l, f, u;
      const g = et(null),
        [h, T] = j(window.innerWidth < 768);
      ie(() => {
        const S = () => {
          T(window.innerWidth < 768);
        };
        return (
          window.addEventListener("resize", S),
          () => {
            window.removeEventListener("resize", S);
          }
        );
      }, []),
        ie(() => {
          var S, k;
          const V = (B) => {
              g.current && !g.current.contains(B.target) && n();
            },
            R = (B) => {
              B.key === "Escape" && n();
            };
          return (
            i &&
            !(
              (k = (S = window.Fides) == null ? void 0 : S.options) != null &&
              k.preventDismissal
            ) &&
            !r
              ? (window.addEventListener("mousedown", V),
                window.addEventListener("keydown", R))
              : (window.removeEventListener("mousedown", V),
                window.removeEventListener("keydown", R)),
            () => {
              window.removeEventListener("mousedown", V),
                window.removeEventListener("keydown", R);
            }
          );
        }, [n, i, g]);
      const m = ae().globalPrivacyControl;
      ie(() => {
        i && e();
      }, [i, e]);
      const C = t.banner_description || t.description,
        O = t.banner_title || t.title;
      return c(
        "div",
        {
          id: "fides-banner-container",
          className: `fides-banner fides-banner-bottom 
        ${i ? "" : "fides-banner-hidden"} 
        ${a || ""}`,
          ref: g,
        },
        c(
          "div",
          { id: "fides-banner" },
          c(
            "div",
            { id: "fides-banner-inner" },
            c($i, {
              ariaLabel: "Close banner",
              onClick: window.Fides.options.fidesPreviewMode ? () => {} : n,
              hidden:
                (l = (p = window.Fides) == null ? void 0 : p.options) == null
                  ? void 0
                  : l.preventDismissal,
            }),
            c(
              "div",
              {
                id: "fides-banner-inner-container",
                style: { gridTemplateColumns: s ? "1fr 1fr" : "1fr" },
              },
              c(
                "div",
                { id: "fides-banner-inner-description" },
                c(
                  "div",
                  { id: "fides-banner-heading" },
                  c(
                    "div",
                    {
                      id: "fides-banner-title",
                      className: "fides-banner-title",
                    },
                    O
                  ),
                  m &&
                    c(Fi, {
                      label: "Global Privacy Control Signal",
                      status: "detected",
                    })
                ),
                c(
                  "div",
                  {
                    id: "fides-banner-description",
                    className: "fides-banner-description",
                  },
                  c(Ri, {
                    description: C,
                    onVendorPageClick: o,
                    allowHTMLDescription:
                      (u = (f = window.Fides) == null ? void 0 : f.options) ==
                      null
                        ? void 0
                        : u.allowHTMLDescription,
                  })
                )
              ),
              s,
              !h && d({ isMobile: h })
            ),
            h && d({ isMobile: h })
          )
        )
      );
    };
  function $r(t, e) {
    e === void 0 && (e = {});
    var n = e.insertAt;
    if (!(!t || typeof document > "u")) {
      var i = document.head || document.getElementsByTagName("head")[0],
        s = document.createElement("style");
      (s.type = "text/css"),
        n === "top" && i.firstChild
          ? i.insertBefore(s, i.firstChild)
          : i.appendChild(s),
        s.styleSheet
          ? (s.styleSheet.cssText = t)
          : s.appendChild(document.createTextNode(t));
    }
  }
  var Fr = `:root{--fides-overlay-primary-color:#8243f2;--fides-overlay-background-color:#f7fafc;--fides-overlay-embed-background-color:transparent;--fides-overlay-font-color:#4a5568;--fides-overlay-font-color-dark:#2d3748;--fides-overlay-hover-color:#edf2f7;--fides-overlay-gpc-applied-background-color:#38a169;--fides-overlay-gpc-applied-text-color:#fff;--fides-overlay-gpc-overridden-background-color:#e53e3e;--fides-overlay-gpc-overridden-text-color:#fff;--fides-overlay-background-dark-color:#e2e8f0;--fides-overlay-width:680px;--fides-overlay-primary-button-background-color:var(
    --fides-overlay-primary-color
  );--fides-overlay-primary-button-background-hover-color:#9569f4;--fides-overlay-primary-button-text-color:#fff;--fides-overlay-primary-button-border-color:transparent;--fides-overlay-secondary-button-background-color:var(
    --fides-overlay-background-color
  );--fides-overlay-secondary-button-background-hover-color:var(
    --fides-overlay-hover-color
  );--fides-overlay-secondary-button-text-color:#2d3748;--fides-overlay-secondary-button-border-color:var(
    --fides-overlay-primary-color
  );--fides-overlay-title-font-color:var(--fides-overlay-font-color);--fides-overlay-body-font-color:var(--fides-overlay-font-color);--fides-overlay-link-font-color:var(--fides-overlay-font-color-dark);--fides-overlay-primary-active-color:var(--fides-overlay-primary-color);--fides-overlay-primary-active-disabled-color:#bda4f7;--fides-overlay-inactive-color:#e2e8f0;--fides-overlay-inactive-font-color:#a0aec0;--fides-overlay-disabled-color:#e1e7ee;--fides-overlay-row-divider-color:#e2e8f0;--fides-overlay-row-hover-color:var(--fides-overlay-hover-color);--fides-overlay-badge-background-color:#718096;--fides-overlay-badge-border-radius:4px;--fides-overlay-select-border-color:#e2e8f0;--fides-overlay-font-family:Inter,sans-serif;--12px:0.75rem;--14px:0.875rem;--15px:0.9375rem;--16px:1rem;--fides-overlay-font-size-body-small:var(--12px);--fides-overlay-font-size-body:var(--14px);--fides-overlay-font-size-title:var(--16px);--fides-overlay-font-size-buttons:var(--14px);--fides-overlay-padding:24px;--fides-overlay-button-border-radius:6px;--fides-overlay-button-padding:8px 16px;--fides-overlay-container-border-radius:12px;--fides-overlay-component-border-radius:4px;--fides-overlay-banner-offset:48px;--fides-banner-font-size-title:var(--16px)}div#fides-overlay{-webkit-font-smoothing:antialiased;font-family:var(--fides-overlay-font-family);font-size:var(--fides-overlay-font-size-body);line-height:calc(1em + .4rem);position:fixed;white-space:pre-line;z-index:1000}#fides-modal-link{cursor:pointer;display:none}#fides-modal-link.fides-modal-link-shown{display:inline}div#fides-banner-container{display:flex;justify-content:center;position:fixed;transform:translateY(0);transition:transform 1s,visibility 1s;visibility:visible;width:100%;z-index:1}div#fides-banner{align-items:center;background:var(--fides-overlay-background-color);border-top:1px solid var(--fides-overlay-primary-color);box-sizing:border-box;color:var(--fides-overlay-body-font-color);display:flex;flex-direction:row;flex-wrap:wrap;font-size:var(--fides-overlay-font-size-body);justify-content:space-between;overflow-y:hidden;padding:24px;position:relative}div#fides-banner-inner{width:100%}div#fides-banner-container.fides-banner-bottom{bottom:0;left:0}div#fides-banner-container.fides-banner-bottom.fides-banner-hidden{transform:translateY(150%);visibility:hidden}div#fides-banner-container.fides-banner-top{left:0;top:0}div#fides-banner-container.fides-banner-top.fides-banner-hidden{transform:translateY(-150%);visibility:hidden}div#fides-banner-inner div#fides-button-group{margin-bottom:0;margin-top:0;padding-bottom:0;padding-top:0;width:100%}div#fides-banner-inner-container{grid-column-gap:60px;display:grid;grid-template-columns:1fr 1fr;.fides-acknowledge-button-container{margin-bottom:0}}div#fides-banner-inner-description{grid-column:1;grid-row:1}div#fides-tcf-banner-inner{grid-column:2;grid-row:1/3;height:0;margin-top:40px;min-height:100%;overflow-y:auto;scrollbar-gutter:stable}div#fides-banner-heading{align-items:center;display:flex;margin-right:13px}div#fides-banner-title{color:var(--fides-overlay-title-font-color);flex:1;font-size:var(--fides-banner-font-size-title);font-weight:600;line-height:1.5em;min-width:33%}div#fides-banner-description{flex:1;font-size:var(--fides-overlay-font-size-body);margin-bottom:24px;margin-top:16px}div.fides-html-description{white-space:normal}div#fides-button-group{background-color:var(--fides-overlay-background-color);display:flex;justify-content:space-between;margin-bottom:var(--fides-overlay-padding);margin-top:8px;z-index:5}div.fides-acknowledge-button-container{display:flex;justify-content:end;margin-inline:var(--fides-overlay-padding);margin-bottom:var(--fides-overlay-padding)}div.fides-banner-acknowledge .fides-banner-button{max-width:168px}button.fides-banner-button{background:var(--fides-overlay-primary-button-background-color);border:1px solid;border-radius:var(--fides-overlay-button-border-radius);color:var(--fides-overlay-primary-button-text-color);cursor:pointer;display:inline-block;flex:auto;font-family:var(--fides-overlay-font-family);font-size:var(--fides-overlay-font-size-buttons);font-weight:600;margin:4px 0 0;padding:var(--fides-overlay-button-padding);text-align:center;text-decoration:none}button.fides-banner-button:hover{background:var(--fides-overlay-primary-button-background-hover-color)}button.fides-banner-button.fides-banner-button-primary{background:var(--fides-overlay-primary-button-background-color);border:none;color:var(--fides-overlay-primary-button-text-color)}button.fides-banner-button.fides-banner-button-primary:hover{background:var(--fides-overlay-primary-button-background-hover-color)}button.fides-banner-button.fides-banner-button-secondary{background:var(--fides-overlay-secondary-button-background-color);border:1px solid var(--fides-overlay-primary-button-background-color);color:var(--fides-overlay-secondary-button-text-color)}button.fides-banner-button.fides-banner-button-secondary:hover{background:var(--fides-overlay-secondary-button-background-hover-color)}button.fides-banner-button.fides-banner-button-tertiary{background:none;border:none;color:var(--fides-overlay-link-font-color);cursor:pointer;font-size:var(--fides-overlay-font-size-body);font-weight:500;line-height:1.25em;padding:0;text-decoration:underline}div.fides-modal-content{background-color:var(--fides-overlay-background-color);border:1px solid var(--fides-overlay-primary-color);border-radius:var(--fides-overlay-container-border-radius);box-sizing:border-box;color:var(--fides-overlay-body-font-color);display:flex;flex-direction:column;font-family:var(--fides-overlay-font-family);font-size:var(--fides-overlay-font-size-body);left:50%;max-height:680px;overflow:hidden;padding:0;position:fixed;top:50%;transform:translate(-50%,-50%);width:var(--fides-overlay-width);z-index:2}.fides-modal-container,.fides-modal-overlay{background-color:rgba(0,0,0,.25);bottom:0;left:0;position:fixed;right:0;top:0}div#fides-embed-container div#fides-consent-content .fides-modal-footer{position:inherit}div#fides-embed-container .fides-modal-body{padding-top:16px}div#fides-embed-container div#fides-consent-content{background-color:var(--fides-overlay-background-color);border:none;border-radius:var(--fides-overlay-container-border-radius);border-bottom-left-radius:0;border-bottom-right-radius:0;box-sizing:border-box;color:var(--fides-overlay-body-font-color);display:flex;flex-direction:column;font-family:var(--fides-overlay-font-family);font-size:var(--fides-overlay-font-size-body);left:50%;max-height:none;overflow:hidden;padding:0;position:static;top:50%;transform:none;width:var(--fides-overlay-width)}.fides-modal-container{display:flex;z-index:2}.fides-modal-container[aria-hidden=true]{display:none}div#fides-modal .fides-modal-header{display:flex;justify-content:end}div#fides-consent-content{overflow:auto;scrollbar-gutter:stable}div#fides-consent-content .fides-modal-title{color:var(--fides-overlay-title-font-color);font-size:var(--fides-overlay-font-size-title);font-weight:600;margin:0;text-align:center}div#fides-consent-content .fides-modal-body{height:100%;overflow-y:auto;padding-inline:var(--fides-overlay-padding)}.fides-modal-footer{background-color:var(--fides-overlay-background-color);border-bottom-left-radius:var(--fides-overlay-component-border-radius);border-bottom-right-radius:var(--fides-overlay-component-border-radius);bottom:0;display:flex;flex-direction:column;width:var(--fides-overlay-width);z-index:5}div#fides-consent-content .fides-modal-description{margin:8px 0 24px}.fides-banner-button-group{display:flex;gap:12px}.fides-modal-button-group{display:flex;flex-direction:row;gap:12px;margin-inline:var(--fides-overlay-padding);width:100%}.fides-tcf-banner-container div#fides-banner div#fides-banner-inner div#fides-button-group{gap:12px}@media (max-width:48em){div#fides-consent-content,div.fides-modal-content{width:100%!important}.fides-modal-button-group{flex-direction:column}button.fides-banner-button{margin:0 8px 12px 0}}div#fides-banner .fides-close-button{background:none;border:none;cursor:pointer;display:flex;position:absolute;right:3px;top:8px}.fides-modal-header .fides-close-button{background:none;border:none;cursor:pointer;padding-right:8px;padding-top:8px}.fides-close-button:hover{background:var(--fides-overlay-hover-color)}.fides-modal-notices{margin-bottom:16px}div#fides-banner-inner .fides-privacy-policy{margin-bottom:0}.fides-privacy-policy,div#fides-banner-inner .fides-privacy-policy{color:var(--fides-overlay-primary-color);display:block;text-align:center}.fides-privacy-policy{font-family:var(--fides-overlay-font-family);margin-bottom:var(--fides-overlay-padding)}@media (prefers-reduced-motion:reduce){.fides-toggle-display{transition-duration:0ms}}.fides-toggle{align-items:center;display:inline-flex;flex-wrap:wrap;gap:1ch;position:relative}.fides-toggle .fides-toggle-input{cursor:pointer;height:100%;opacity:0;position:absolute;width:100%;z-index:4}.fides-toggle .fides-toggle-display{--offset:4px;--diameter:16px;align-items:center;background-color:var(--fides-overlay-inactive-color);border-radius:100vw;box-sizing:content-box;color:var(--fides-overlay-inactive-font-color);display:inline-flex!important;height:24px;justify-content:space-around;justify-content:end;padding-inline:8px;position:relative;transition:.25s;width:34px}.fides-toggle .fides-toggle-display:before{background-color:#fff;border-radius:50%;box-shadow:0 1.3px 2.7px rgba(0,0,0,.25);box-sizing:border-box;content:"";height:var(--diameter);left:var(--offset);position:absolute;top:50%;transform:translateY(-50%);transition:inherit;width:var(--diameter);z-index:3}.fides-toggle .fides-toggle-input:checked+.fides-toggle-display{background-color:var(--fides-overlay-primary-active-color);color:var(--fides-overlay-primary-button-text-color);justify-content:start}.fides-toggle .fides-toggle-input:checked+.fides-toggle-display:before{transform:translate(26px,-50%)}.fides-toggle .fides-toggle-input:disabled{cursor:not-allowed}.fides-toggle .fides-toggle-input:disabled+.fides-toggle-display{background-color:var(--fides-overlay-disabled-color)}.fides-toggle .fides-toggle-input:disabled:checked+.fides-toggle-display{background-color:var(--fides-overlay-primary-active-disabled-color)}.fides-toggle .fides-toggle-input:focus+.fides-toggle-display{outline:1px auto Highlight;outline:1px auto -webkit-focus-ring-color}.fides-toggle .fides-toggle-input:focus:not(:focus-visible)+.fides-toggle-display{outline:0}.fides-divider{border-color:var(--fides-overlay-row-divider-color);border-width:0 0 1px;margin:0}.fides-disclosure-hidden{display:flex;height:0;margin-bottom:0;margin-top:0;overflow:hidden;visibility:hidden}.fides-notice-toggle .fides-notice-toggle-title{align-items:center;border-bottom:1px solid var(--fides-overlay-row-divider-color);display:flex;justify-content:space-between;padding-inline:12px 12px}.fides-notice-toggle .fides-notice-toggle-trigger{align-items:center;display:flex;justify-content:space-between;min-height:40px;width:100%}.fides-notice-toggle .fides-notice-toggle-trigger svg{flex-shrink:0}.fides-notice-toggle .fides-notice-toggle-title:hover{background-color:var(--fides-overlay-row-hover-color);cursor:pointer}#fides-tcf-banner-inner .fides-disclosure-visible{padding:12px}.fides-notice-toggle .fides-disclosure-visible{display:flex;flex-direction:column;gap:12px;overflow:auto;padding:12px}.fides-notice-toggle p{margin:0 0 18px}.fides-notice-toggle p:last-child{margin:0}.fides-notice-toggle-title .fides-flex-center{align-items:center;display:flex;white-space:wrap;width:100%}.fides-notice-toggle-expanded{background-color:var(--fides-overlay-row-hover-color)}.fides-notice-toggle-header{font-weight:600}.fides-record-header{border-bottom:1px solid var(--fides-overlay-row-divider-color);font-weight:600;padding:12px}.fides-gpc-banner{border:1px solid var(--fides-overlay-primary-color);border-radius:var(--fides-overlay-component-border-radius);display:flex;margin-bottom:16px;padding:18px}.fides-gpc-banner p{margin:0}.fides-gpc-warning{color:var(--fides-overlay-primary-color);margin-right:8px}.fides-gpc-header{font-weight:700}.fides-gpc-label{text-wrap:nowrap;font-size:var(--fides-overlay-font-size-body);font-weight:600}.fides-gpc-badge{border-radius:var(--fides-overlay-badge-border-radius);font-weight:700;padding:0 4px;text-transform:uppercase}.fides-gpc-badge-applied,.fides-gpc-badge-detected{background:var(--fides-overlay-gpc-applied-background-color);color:var(--fides-overlay-gpc-applied-text-color)}.fides-gpc-badge-overridden{background:var(--fides-overlay-gpc-overridden-background-color);color:var(--fides-overlay-gpc-overridden-text-color)}.fides-tab-list{display:flex;list-style-type:none;padding:0}.fides-tab-list>li{width:100%}.fides-tab-button{background:none;border-width:0 0 1px;border-bottom:1px solid var(--fides-overlay-row-divider-color);color:var(--fides-overlay-body-font-color);cursor:pointer;font-weight:500;padding:10px 20px;width:100%}.fides-tab-button[aria-selected=true]{border-bottom-width:2px;border-color:var(--fides-overlay-primary-active-color);color:var(--fides-overlay-primary-active-color);font-weight:600}.fides-tab-button::focus-visible{outline:1px auto Highlight;outline:1px auto -webkit-focus-ring-color}.fides-tab-button:focus:not(:focus-visible){outline:0}.fides-notice-badge{align-items:center;background:var(--fides-overlay-badge-background-color);border-radius:var(--fides-overlay-badge-border-radius);color:#fff;display:inline-flex;font-size:var(--fides-overlay-font-size-body-small);font-weight:600;height:18px;margin-right:8px;padding:0 4px;text-transform:uppercase}.fides-background-dark{background-color:var(--fides-overlay-background-dark-color)}.fides-radio-button-group{background-color:var(
    --fides-overlay-secondary-button-background-hover-color
  );border:1px solid var(--fides-overlay-row-divider-color);display:flex;margin-bottom:22px;padding:4px}.fides-radio-button{background-color:transparent;border:none;cursor:pointer;flex:1;padding:5px 16px}.fides-radio-button[aria-checked=true]{background-color:var(--fides-overlay-primary-button-background-color);color:var(--fides-overlay-primary-button-text-color)}.fides-flex-center{align-items:center;display:flex}.fides-margin-right{margin-right:3px}.fides-justify-space-between{justify-content:space-between}.fides-tcf-toggle-content{font-size:var(--fides-overlay-font-size-body-small);font-weight:400;margin-right:60px}.fides-tcf-purpose-vendor-title{display:flex;font-weight:600;justify-content:space-between}.fides-tcf-illustration{font-size:var(--fides-overlay-font-size-body-small);padding:13px 60px 13px 13px}.fides-tcf-illustration,.fides-tcf-purpose-vendor{border-radius:var(--fides-overlay-component-border-radius)}.fides-tcf-purpose-vendor{padding:13px}.fides-tcf-purpose-vendor-list{font-weight:400;list-style:none;margin-bottom:0;margin-left:0;padding-left:0}.fides-tcf-vendor-toggles{display:flex}.fides-vendor-details-table{width:100%}.fides-vendor-details-table td,.fides-vendor-details-table th{font-size:var(--fides-overlay-font-size-body-small);text-align:left}.fides-vendor-details-table td{border-bottom:1px solid var(--fides-overlay-row-divider-color)}.fides-link-button{background:none;border:none;color:var(--fides-overlay-body-font-color);cursor:pointer;padding:0;text-decoration:underline}.fides-external-link,.fides-primary-text-color{color:var(--fides-overlay-primary-color)}.fides-external-link{font-size:var(--fides-overlay-font-size-body-small);font-weight:500;margin-right:16px}.fides-vendor-info-banner{border-radius:var(--fides-overlay-component-border-radius);display:flex;flex-direction:row;gap:30px;justify-content:space-around;margin-bottom:16px;padding:16px 12px;position:sticky;top:0}.fides-vendor-info-label{font-size:var(--fides-overlay-font-size-body-small);font-weight:600;margin-right:4px}.fides-info-box{background-color:var(--fides-overlay-hover-color);border-radius:var(--fides-overlay-component-border-radius);margin:10px 0;padding:16px}.fides-info-box p{margin:0}.fides-tabs .tabpanel-container{overflow:hidden}.tabpanel-container section[hidden]{display:none}@media screen and (min-width:768px){div#fides-banner{border:1px solid var(--fides-overlay-primary-color);border-radius:var(--fides-overlay-component-border-radius);width:75%}div#fides-banner-container.fides-banner-bottom{bottom:var(--fides-overlay-banner-offset)}}@media only screen and (min-width:1280px){div#fides-banner{border:1px solid var(--fides-overlay-primary-color);width:60%}}@media screen and (max-width:992px){.fides-vendor-info-banner{flex-direction:column;gap:16px}}@media screen and (max-width:768px){div#fides-banner{padding:24px}div#fides-banner-description{margin-bottom:0}div#fides-banner-inner div#fides-button-group{flex-direction:column;gap:12px;padding-top:24px}.fides-banner-button-group{flex-direction:column}button.fides-banner-button{margin:0}div#fides-tcf-banner-inner{margin-top:24px;min-height:revert;overflow-y:revert}div#fides-banner-inner-container{display:flex;flex-direction:column;max-height:50vh;overflow-y:auto;scrollbar-gutter:stable}div#fides-privacy-policy-link{order:1;width:100%}.fides-modal-footer{width:100%}.fides-tcf-banner-container div#fides-banner div#fides-banner-inner div#fides-button-group .fides-banner-button-group{padding-left:0}}.fides-tcf-banner-container{bottom:0!important}.fides-tcf-banner-container #fides-banner{border-radius:0;border-width:1px 0 0;padding:24px 40px 40px;width:100%}.fides-tcf-banner-container #fides-privacy-policy-link{margin:auto}.fides-paging-buttons{display:flex;gap:8px;justify-content:center}.fides-paging-info{color:var(--fides-overlay-font-color-dark);font-size:var(--fides-overlay-font-size-body-small);font-weight:600;padding:8px}.fides-paging-previous-button{margin-right:8px}.fides-paging-next-button,.fides-paging-previous-button{background-color:transparent;border:none;cursor:pointer;padding:6px}.fides-paging-next-button:disabled,.fides-paging-previous-button:disabled{cursor:default}`;
  $r(Fr);
  var Rr = [
      'a[href]:not([tabindex^="-"])',
      'area[href]:not([tabindex^="-"])',
      'input:not([type="hidden"]):not([type="radio"]):not([disabled]):not([tabindex^="-"])',
      'input[type="radio"]:not([disabled]):not([tabindex^="-"])',
      'select:not([disabled]):not([tabindex^="-"])',
      'textarea:not([disabled]):not([tabindex^="-"])',
      'button:not([disabled]):not([tabindex^="-"])',
      'iframe:not([tabindex^="-"])',
      'audio[controls]:not([tabindex^="-"])',
      'video[controls]:not([tabindex^="-"])',
      '[contenteditable]:not([tabindex^="-"])',
      '[tabindex]:not([tabindex^="-"])',
    ],
    Vr = "Tab",
    Dr = "Escape";
  function Y(t) {
    (this._show = this.show.bind(this)),
      (this._hide = this.hide.bind(this)),
      (this._maintainFocus = this._maintainFocus.bind(this)),
      (this._bindKeypress = this._bindKeypress.bind(this)),
      (this.$el = t),
      (this.shown = !1),
      (this._id = this.$el.getAttribute("data-a11y-dialog") || this.$el.id),
      (this._previouslyFocused = null),
      (this._listeners = {}),
      this.create();
  }
  (Y.prototype.create = function () {
    this.$el.setAttribute("aria-hidden", !0),
      this.$el.setAttribute("aria-modal", !0),
      this.$el.setAttribute("tabindex", -1),
      this.$el.hasAttribute("role") || this.$el.setAttribute("role", "dialog"),
      (this._openers = Re('[data-a11y-dialog-show="' + this._id + '"]')),
      this._openers.forEach(
        function (e) {
          e.addEventListener("click", this._show);
        }.bind(this)
      );
    const t = this.$el;
    return (
      (this._closers = Re("[data-a11y-dialog-hide]", this.$el)
        .filter(function (e) {
          return e.closest('[aria-modal="true"], [data-a11y-dialog]') === t;
        })
        .concat(Re('[data-a11y-dialog-hide="' + this._id + '"]'))),
      this._closers.forEach(
        function (e) {
          e.addEventListener("click", this._hide);
        }.bind(this)
      ),
      this._fire("create"),
      this
    );
  }),
    (Y.prototype.show = function (t) {
      return this.shown
        ? this
        : ((this._previouslyFocused = document.activeElement),
          this.$el.removeAttribute("aria-hidden"),
          (this.shown = !0),
          Vi(this.$el),
          document.body.addEventListener("focus", this._maintainFocus, !0),
          document.addEventListener("keydown", this._bindKeypress),
          this._fire("show", t),
          this);
    }),
    (Y.prototype.hide = function (t) {
      return this.shown
        ? ((this.shown = !1),
          this.$el.setAttribute("aria-hidden", "true"),
          this._previouslyFocused &&
            this._previouslyFocused.focus &&
            this._previouslyFocused.focus(),
          document.body.removeEventListener("focus", this._maintainFocus, !0),
          document.removeEventListener("keydown", this._bindKeypress),
          this._fire("hide", t),
          this)
        : this;
    }),
    (Y.prototype.destroy = function () {
      return (
        this.hide(),
        this._openers.forEach(
          function (t) {
            t.removeEventListener("click", this._show);
          }.bind(this)
        ),
        this._closers.forEach(
          function (t) {
            t.removeEventListener("click", this._hide);
          }.bind(this)
        ),
        this._fire("destroy"),
        (this._listeners = {}),
        this
      );
    }),
    (Y.prototype.on = function (t, e) {
      return (
        typeof this._listeners[t] > "u" && (this._listeners[t] = []),
        this._listeners[t].push(e),
        this
      );
    }),
    (Y.prototype.off = function (t, e) {
      var n = (this._listeners[t] || []).indexOf(e);
      return n > -1 && this._listeners[t].splice(n, 1), this;
    }),
    (Y.prototype._fire = function (t, e) {
      var n = this._listeners[t] || [],
        i = new CustomEvent(t, { detail: e });
      this.$el.dispatchEvent(i),
        n.forEach(
          function (s) {
            s(this.$el, e);
          }.bind(this)
        );
    }),
    (Y.prototype._bindKeypress = function (t) {
      const e = document.activeElement;
      (e && e.closest('[aria-modal="true"]') !== this.$el) ||
        (this.shown &&
          t.key === Dr &&
          this.$el.getAttribute("role") !== "alertdialog" &&
          (t.preventDefault(), this.hide(t)),
        this.shown && t.key === Vr && jr(this.$el, t));
    }),
    (Y.prototype._maintainFocus = function (t) {
      this.shown &&
        !t.target.closest('[aria-modal="true"]') &&
        !t.target.closest("[data-a11y-dialog-ignore-focus-trap]") &&
        Vi(this.$el);
    });
  function Ur(t) {
    return Array.prototype.slice.call(t);
  }
  function Re(t, e) {
    return Ur((e || document).querySelectorAll(t));
  }
  function Vi(t) {
    var e = t.querySelector("[autofocus]") || t;
    e.focus();
  }
  function Mr(t) {
    return Re(Rr.join(","), t).filter(function (e) {
      return !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length);
    });
  }
  function jr(t, e) {
    var n = Mr(t),
      i = n.indexOf(document.activeElement);
    e.shiftKey && i === 0
      ? (n[n.length - 1].focus(), e.preventDefault())
      : !e.shiftKey && i === n.length - 1 && (n[0].focus(), e.preventDefault());
  }
  function Vt() {
    Re("[data-a11y-dialog]").forEach(function (t) {
      new Y(t);
    });
  }
  typeof document < "u" &&
    (document.readyState === "loading"
      ? document.addEventListener("DOMContentLoaded", Vt)
      : window.requestAnimationFrame
      ? window.requestAnimationFrame(Vt)
      : window.setTimeout(Vt, 16));
  const Br = (t) => {
      const [e, n] = j(null),
        i = L((s) => {
          if (s !== null) {
            const o = new Y(s);
            o
              .on("show", () => {
                document.documentElement.style.overflowY = "hidden";
              })
              .on("hide", (d, a) => {
                (document.documentElement.style.overflowY = ""),
                  t && a instanceof KeyboardEvent && a.key === "Escape" && t();
              }),
              n(o);
          }
        }, []);
      return { instance: e, container: i };
    },
    Hr = ({ role: t, id: e, onClose: n, onEsc: i }) => {
      const { instance: s, container: o } = Br(i),
        d = t === "alertdialog",
        a = `${e}-title`,
        r = L(() => {
          s && s.hide(), n && n();
        }, [s]);
      return (
        ie(
          () => () => {
            s && s.destroy();
          },
          [s]
        ),
        {
          instance: s,
          attributes: {
            container: {
              id: e,
              ref: o,
              role: t,
              tabIndex: -1,
              "aria-modal": !0,
              "aria-hidden": !0,
              "aria-labelledby": a,
            },
            overlay: { onClick: d ? void 0 : r },
            dialog: { role: "document" },
            closeButton: { type: "button", onClick: r },
            title: { role: "heading", "aria-level": 1, id: a },
          },
        }
      );
    },
    zr = () =>
      c(
        "svg",
        {
          xmlns: "http://www.w3.org/2000/svg",
          width: "18",
          height: "18",
          fill: "currentColor",
        },
        c("path", {
          d: "M9 12.05a.68.68 0 0 0-.68.7c0 .39.32.7.68.7.39 0 .68-.31.68-.7a.66.66 0 0 0-.68-.7Zm0-1.18c.26 0 .44-.2.44-.46V6.19c0-.26-.2-.47-.44-.47a.49.49 0 0 0-.47.47v4.22c0 .25.21.46.47.46Zm7.27 2.27-5.85-9.9c-.3-.5-.83-.8-1.42-.8-.6 0-1.12.3-1.42.8l-5.86 9.9c-.3.5-.3 1.1-.01 1.6.3.51.83.82 1.43.82h11.72c.6 0 1.13-.3 1.43-.82.29-.5.28-1.1-.02-1.6Zm-.82 1.1c-.1.25-.33.38-.62.38H3.14a.7.7 0 0 1-.61-.35.64.64 0 0 1 0-.65l5.86-9.9A.7.7 0 0 1 9 3.37a.7.7 0 0 1 .61.35l5.86 9.9c.1.2.12.44-.02.63Z",
        })
      ),
    Gr = () =>
      ae().globalPrivacyControl
        ? c(
            "div",
            { className: "fides-gpc-banner" },
            c("div", { className: "fides-gpc-warning" }, c(zr, null)),
            c(
              "div",
              null,
              c(
                "p",
                { className: "fides-gpc-header" },
                "Global Privacy Control detected"
              ),
              c(
                "p",
                null,
                "Your global privacy control preference has been honored. You have been automatically opted out of data uses cases which adhere to global privacy control."
              )
            )
          )
        : null;
  var Kr = Object.defineProperty,
    Yr = Object.defineProperties,
    qr = Object.getOwnPropertyDescriptors,
    Di = Object.getOwnPropertySymbols,
    Wr = Object.prototype.hasOwnProperty,
    Qr = Object.prototype.propertyIsEnumerable,
    Ui = (t, e, n) =>
      e in t
        ? Kr(t, e, { enumerable: !0, configurable: !0, writable: !0, value: n })
        : (t[e] = n),
    Jr = (t, e) => {
      for (var n in e || (e = {})) Wr.call(e, n) && Ui(t, n, e[n]);
      if (Di) for (var n of Di(e)) Qr.call(e, n) && Ui(t, n, e[n]);
      return t;
    },
    Zr = (t, e) => Yr(t, qr(e));
  const Mi = ({
    title: t,
    className: e,
    experience: n,
    renderModalFooter: i,
    children: s,
    onVendorPageClick: o,
  }) => {
    var d, a;
    const r = ae().globalPrivacyControl;
    return c(
      K,
      null,
      c(
        "div",
        {
          "data-testid": "consent-content",
          id: "fides-consent-content",
          className: e,
        },
        c(
          "div",
          { className: "fides-modal-body" },
          c(
            "div",
            Zr(Jr({ "data-testid": "fides-modal-title" }, t), {
              className: "fides-modal-title",
            }),
            n.title
          ),
          c(
            "p",
            {
              "data-testid": "fides-modal-description",
              className: "fides-modal-description",
            },
            c(Ri, {
              onVendorPageClick: o,
              description: n.description,
              allowHTMLDescription:
                (a = (d = window.Fides) == null ? void 0 : d.options) == null
                  ? void 0
                  : a.allowHTMLDescription,
            })
          ),
          r && c(Gr, null),
          s
        )
      ),
      c("div", { className: "fides-modal-footer" }, i())
    );
  };
  var Xr = Object.defineProperty,
    ea = Object.defineProperties,
    ta = Object.getOwnPropertyDescriptors,
    ji = Object.getOwnPropertySymbols,
    na = Object.prototype.hasOwnProperty,
    ia = Object.prototype.propertyIsEnumerable,
    Bi = (t, e, n) =>
      e in t
        ? Xr(t, e, { enumerable: !0, configurable: !0, writable: !0, value: n })
        : (t[e] = n),
    Dt = (t, e) => {
      for (var n in e || (e = {})) na.call(e, n) && Bi(t, n, e[n]);
      if (ji) for (var n of ji(e)) ia.call(e, n) && Bi(t, n, e[n]);
      return t;
    },
    Ut = (t, e) => ea(t, ta(e));
  const sa = ({
    attributes: t,
    experience: e,
    renderModalFooter: n,
    renderModalContent: i,
  }) => {
    const { container: s, overlay: o, dialog: d, title: a, closeButton: r } = t;
    return c(
      "div",
      Ut(Dt({ "data-testid": "consent-modal" }, s), {
        className: "fides-modal-container",
      }),
      c("div", Ut(Dt({}, o), { className: "fides-modal-overlay" })),
      c(
        "div",
        Ut(Dt({ "data-testid": "fides-modal-content" }, d), {
          className: "fides-modal-content",
        }),
        c(
          "div",
          { className: "fides-modal-header" },
          c("div", null),
          c($i, {
            ariaLabel: "Close modal",
            onClick: window.Fides.options.fidesPreviewMode
              ? () => {}
              : r.onClick,
            hidden: window.Fides.options.preventDismissal,
          })
        ),
        c(Mi, { title: a, experience: e, renderModalFooter: n }, i())
      )
    );
  };
  var oa = (t, e, n) =>
    new Promise((i, s) => {
      var o = (r) => {
          try {
            a(n.next(r));
          } catch (p) {
            s(p);
          }
        },
        d = (r) => {
          try {
            a(n.throw(r));
          } catch (p) {
            s(p);
          }
        },
        a = (r) => (r.done ? i(r.value) : Promise.resolve(r.value).then(o, d));
      a((n = n.apply(t, e)).next());
    });
  const ra = () => {
      const [t, e] = j(!1);
      return (
        ie(() => {
          e(!0);
        }, []),
        t
      );
    },
    Hi = ({ id: t }) => {
      const [e, n] = j(!1),
        i = L(() => n(!1), []),
        s = L(() => n(!0), []),
        o = L(() => {
          e ? i() : s();
        }, [e, s, i]);
      return {
        isOpen: e,
        onOpen: s,
        onClose: i,
        onToggle: o,
        getButtonProps: () => ({
          "aria-expanded": e,
          "aria-controls": t,
          onClick: o,
        }),
        getDisclosureProps: () => ({
          id: t,
          className: e ? "fides-disclosure-visible" : "fides-disclosure-hidden",
        }),
      };
    },
    se = (t) => (t ? t.map((e) => e.id) : []),
    zi = ({
      notices: t,
      options: e,
      userGeography: n,
      privacyExperience: i,
      acknowledgeMode: s,
    }) => {
      const [o, d] = j(null),
        a = L(
          (r) =>
            oa(void 0, null, function* () {
              if (
                e.fidesPreviewMode ||
                !r.detail.extraDetails ||
                r.detail.extraDetails.servingComponent === ue.BANNER
              )
                return;
              const p = {
                  browser_identity: r.detail.identity,
                  privacy_experience_id: i.id,
                  user_geography: n,
                  acknowledge_mode: s,
                  privacy_notice_history_ids: t.map(
                    (f) => f.privacy_notice_history_id
                  ),
                  tcf_purpose_consents: se(i?.tcf_purpose_consents),
                  tcf_purpose_legitimate_interests: se(
                    i.tcf_purpose_legitimate_interests
                  ),
                  tcf_special_purposes: se(i?.tcf_special_purposes),
                  tcf_vendor_consents: se(i?.tcf_vendor_consents),
                  tcf_vendor_legitimate_interests: se(
                    i.tcf_vendor_legitimate_interests
                  ),
                  tcf_features: se(i?.tcf_features),
                  tcf_special_features: se(i?.tcf_special_features),
                  tcf_system_consents: se(i?.tcf_system_consents),
                  tcf_system_legitimate_interests: se(
                    i?.tcf_system_legitimate_interests
                  ),
                  serving_component: r.detail.extraDetails.servingComponent,
                },
                l = yield or({ request: p, options: e });
              l && d(l);
            }),
          [t, e, s, i, n]
        );
      return (
        ie(
          () => (
            window.addEventListener("FidesUIShown", a),
            () => {
              window.removeEventListener("FidesUIShown", a);
            }
          ),
          [a]
        ),
        { servedNotice: o }
      );
    },
    Gi = ({
      experience: t,
      options: e,
      cookie: n,
      onOpen: i,
      onDismiss: s,
      renderBanner: o,
      renderModalContent: d,
      renderModalFooter: a,
      onVendorPageClick: r,
    }) => {
      var p;
      const l = ra(),
        [f, u] = j(!1),
        g = L(
          ({ saved: k = !1 }) => {
            U("FidesModalClosed", n, e.debug, { saved: k }), k || s();
          },
          [n, s, e.debug]
        ),
        { instance: h, attributes: T } = Hr({
          id: "fides-modal",
          role: window.Fides.options.preventDismissal
            ? "alertdialog"
            : "dialog",
          title: ((p = t?.experience_config) == null ? void 0 : p.title) || "",
          onClose: () => {
            g({ saved: !1 });
          },
          onEsc: () => {
            g({ saved: !1 });
          },
        }),
        m = L(() => {
          h && (h.show(), i());
        }, [h, i]),
        C = L(() => {
          h && !e.fidesEmbed && (h.hide(), g({ saved: !0 }));
        }, [h, g, e.fidesEmbed]);
      ie(() => {
        e.fidesEmbed && i();
      }, [e, i]),
        ie(() => {
          const k = setTimeout(() => {
            u(!0);
          }, 100);
          return () => clearTimeout(k);
        }, [u]),
        ie(() => {
          const k = setTimeout(() => {
            const V = e.modalLinkId || "fides-modal-link",
              R = document.getElementById(V);
            if (R) {
              b(
                e.debug,
                "Modal link element found, updating it to show and trigger modal on click."
              );
              const B = R;
              (B.onclick = () => {
                u(!1), m();
              }),
                B.classList.add("fides-modal-link-shown");
            } else b(e.debug, "Modal link element not found.");
          }, 200);
          return () => clearTimeout(k);
        }, [e.modalLinkId, e.debug, m]);
      const O = F(
          () =>
            !e.fidesDisableBanner && t.show_banner && Pn(t, n) && !e.fidesEmbed,
          [n, t, e]
        ),
        S = () => {
          m(), u(!1);
        };
      return l
        ? t.experience_config
          ? c(
              "div",
              null,
              O &&
                f &&
                window.Fides.options.preventDismissal &&
                c("div", { className: "fides-modal-overlay" }),
              O
                ? o({
                    isOpen: f,
                    onClose: () => {
                      u(!1);
                    },
                    onSave: () => {
                      u(!1);
                    },
                    onManagePreferencesClick: S,
                  })
                : null,
              e.fidesEmbed
                ? c(
                    Mi,
                    {
                      title: T.title,
                      className: "fides-embed",
                      experience: t.experience_config,
                      renderModalFooter: () => a({ onClose: C, isMobile: !1 }),
                    },
                    d()
                  )
                : c(sa, {
                    attributes: T,
                    experience: t.experience_config,
                    onVendorPageClick: r,
                    renderModalFooter: () => a({ onClose: C, isMobile: !1 }),
                    renderModalContent: d,
                  })
            )
          : (b(e.debug, "No experience config found"), null)
        : null;
    },
    Ee = ({ buttonType: t, label: e, onClick: n, className: i = "" }) =>
      c(
        "button",
        {
          type: "button",
          id: `fides-banner-button-${t.valueOf()}`,
          className: `fides-banner-button fides-banner-button-${t.valueOf()} ${i}`,
          onClick: n,
          "data-testid": `${e}-btn`,
        },
        e || ""
      ),
    Mt = ({ experience: t }) =>
      !(t != null && t.privacy_policy_link_label) ||
      !(t != null && t.privacy_policy_url)
        ? null
        : c(
            "div",
            {
              id: "fides-privacy-policy-link",
              style: {
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              },
            },
            c(
              "a",
              {
                href: t.privacy_policy_url,
                rel: "noopener noreferrer",
                target: "_blank",
                className: "fides-privacy-policy",
              },
              t.privacy_policy_link_label
            )
          ),
    Ki = ({
      experienceConfig: t,
      onManagePreferencesClick: e,
      firstButton: n,
      onAcceptAll: i,
      onRejectAll: s,
      isMobile: o,
      includePrivacyPolicy: d,
      saveOnly: a = !1,
    }) =>
      c(
        "div",
        { id: "fides-button-group" },
        e
          ? c(
              "div",
              { style: { display: "flex" } },
              c(Ee, {
                buttonType: o ? J.SECONDARY : J.TERTIARY,
                label: t.privacy_preferences_link_label,
                onClick: e,
                className: "fides-manage-preferences-button",
              })
            )
          : null,
        d ? c(Mt, { experience: t }) : null,
        c(
          "div",
          {
            className: n
              ? "fides-modal-button-group"
              : "fides-banner-button-group",
          },
          n || null,
          !a &&
            c(
              K,
              null,
              c(Ee, {
                buttonType: J.PRIMARY,
                label: t.reject_button_label,
                onClick: s,
                className: "fides-reject-all-button",
              }),
              c(Ee, {
                buttonType: J.PRIMARY,
                label: t.accept_button_label,
                onClick: i,
                className: "fides-accept-all-button",
              })
            )
        )
      ),
    Yi = ({
      experience: t,
      onSave: e,
      onManagePreferencesClick: n,
      enabledKeys: i,
      isInModal: s,
      isAcknowledge: o,
      isMobile: d,
      saveOnly: a = !1,
      fidesPreviewMode: r = !1,
    }) => {
      if (!t.experience_config || !t.privacy_notices) return null;
      const { experience_config: p, privacy_notices: l } = t,
        f = () => {
          r ||
            e(
              G.ACCEPT,
              l.map((h) => h.notice_key)
            );
        },
        u = () => {
          r ||
            e(
              G.REJECT,
              l
                .filter((h) => h.consent_mechanism === z.NOTICE_ONLY)
                .map((h) => h.notice_key)
            );
        },
        g = () => {
          r || e(G.SAVE, i);
        };
      return o
        ? c(
            "div",
            {
              className: `fides-acknowledge-button-container ${
                s ? "" : "fides-banner-acknowledge"
              }`,
            },
            c(Ee, {
              buttonType: J.PRIMARY,
              label: p.acknowledge_button_label,
              onClick: f,
              className: "fides-acknowledge-button",
            })
          )
        : c(Ki, {
            experienceConfig: p,
            onManagePreferencesClick: n,
            onAcceptAll: f,
            onRejectAll: u,
            firstButton: s
              ? c(Ee, {
                  buttonType: a ? J.PRIMARY : J.SECONDARY,
                  label: p.save_button_label,
                  onClick: g,
                  className: "fides-save-button",
                })
              : void 0,
            isMobile: d,
            includePrivacyPolicy: !s,
            saveOnly: a,
          });
    },
    aa = () => c("hr", { className: "fides-divider" }),
    da = ({ name: t, id: e, checked: n, onChange: i, disabled: s }) => {
      const o = `toggle-${e}`;
      return c(
        "label",
        {
          className: "fides-toggle",
          htmlFor: t,
          "data-testid": `toggle-${t}`,
          id: o,
        },
        c("input", {
          type: "checkbox",
          name: t,
          className: "fides-toggle-input",
          onChange: () => {
            i(e);
          },
          checked: n,
          role: "switch",
          "aria-labelledby": o,
          disabled: s,
        }),
        c(
          "span",
          { className: "fides-toggle-display", hidden: !0 },
          n ? "On" : "Off"
        )
      );
    };
  var la = Object.defineProperty,
    ca = Object.defineProperties,
    pa = Object.getOwnPropertyDescriptors,
    qi = Object.getOwnPropertySymbols,
    ua = Object.prototype.hasOwnProperty,
    fa = Object.prototype.propertyIsEnumerable,
    Wi = (t, e, n) =>
      e in t
        ? la(t, e, { enumerable: !0, configurable: !0, writable: !0, value: n })
        : (t[e] = n),
    Qi = (t, e) => {
      for (var n in e || (e = {})) ua.call(e, n) && Wi(t, n, e[n]);
      if (qi) for (var n of qi(e)) fa.call(e, n) && Wi(t, n, e[n]);
      return t;
    },
    ga = (t, e) => ca(t, pa(e));
  const Ji = ({
      dataUse: t,
      checked: e,
      onToggle: n,
      children: i,
      badge: s,
      gpcBadge: o,
      disabled: d,
      isHeader: a,
      includeToggle: r = !0,
    }) => {
      const {
          isOpen: p,
          getButtonProps: l,
          getDisclosureProps: f,
          onToggle: u,
        } = Hi({ id: t.key }),
        g = (m) => {
          (m.code === "Space" || m.code === "Enter") && u();
        },
        h = i != null,
        T = h ? l() : {};
      return c(
        "div",
        {
          className:
            p && h
              ? "fides-notice-toggle fides-notice-toggle-expanded"
              : "fides-notice-toggle",
        },
        c(
          "div",
          { key: t.key, className: "fides-notice-toggle-title" },
          c(
            "span",
            ga(
              Qi({ role: "button", tabIndex: 0, onKeyDown: h ? g : void 0 }, T),
              {
                className: a
                  ? "fides-notice-toggle-trigger fides-notice-toggle-header"
                  : "fides-notice-toggle-trigger",
              }
            ),
            c(
              "span",
              { className: "fides-flex-center fides-justify-space-between" },
              t.name,
              s ? c("span", { className: "fides-notice-badge" }, s) : null
            ),
            o
          ),
          r
            ? c(da, {
                name: t.name || "",
                id: t.key,
                checked: e,
                onChange: n,
                disabled: d,
              })
            : null
        ),
        i ? c("div", Qi({}, f()), i) : null
      );
    },
    va = ({ notices: t, enabledNoticeKeys: e, onChange: n }) => {
      const i = (s) => {
        e.indexOf(s) === -1 ? n([...e, s]) : n(e.filter((o) => o !== s));
      };
      return c(
        "div",
        null,
        t.map((s, o) => {
          const d = e.indexOf(s.notice_key) !== -1,
            a = o === t.length - 1,
            r = { key: s.notice_key, name: s.name };
          return c(
            "div",
            null,
            c(
              Ji,
              {
                dataUse: r,
                checked: d,
                onToggle: i,
                gpcBadge: c(Nr, { notice: s, value: d }),
                disabled: s.consent_mechanism === z.NOTICE_ONLY,
              },
              s.description
            ),
            a ? null : c(aa, null)
          );
        })
      );
    },
    ha = ({ experience: t, options: e, fidesRegionString: n, cookie: i }) => {
      const s = F(
          () =>
            t.privacy_notices
              ? t.privacy_notices.map((m) =>
                  wt(m, ae(), i) ? m.notice_key : ""
                )
              : [],
          [i, t]
        ),
        [o, d] = j(s),
        a = F(() => {
          var m;
          return (m = t.privacy_notices) != null ? m : [];
        }, [t.privacy_notices]),
        r = a.every((m) => m.consent_mechanism === z.NOTICE_ONLY),
        { servedNotice: p } = zi({
          notices: a,
          options: e,
          userGeography: n,
          acknowledgeMode: r,
          privacyExperience: t,
        }),
        l = (m, C) =>
          m.map((O) => {
            const S = de(C.includes(O.notice_key), O.consent_mechanism);
            return new ze(O, S);
          }),
        f = L(
          (m, C) => {
            const O = l(a, C);
            Pt({
              consentPreferencesToSave: O,
              experience: t,
              consentMethod: m,
              options: e,
              userLocationString: n,
              cookie: i,
              servedNoticeHistoryId: p?.served_notice_history_id,
              updateCookie: (S) => Ot(S, O),
            }),
              d(C);
          },
          [a, i, n, t, e, p]
        ),
        u = L(() => {
          U("FidesUIShown", i, e.debug, { servingComponent: ue.BANNER });
        }, [i, e.debug]),
        g = L(() => {
          U("FidesUIShown", i, e.debug, { servingComponent: ue.OVERLAY });
        }, [i, e.debug]),
        h = L(() => {
          f(G.DISMISS, s);
        }, [f, s]);
      if (!t.experience_config)
        return b(e.debug, "No experience config found"), null;
      const T = t.experience_config;
      return c(Gi, {
        options: e,
        experience: t,
        cookie: i,
        onOpen: g,
        onDismiss: h,
        renderBanner: ({
          isOpen: m,
          onClose: C,
          onSave: O,
          onManagePreferencesClick: S,
        }) =>
          c(Rt, {
            bannerIsOpen: m,
            fidesPreviewMode: e.fidesPreviewMode,
            onOpen: u,
            onClose: () => {
              C(), h();
            },
            experience: T,
            renderButtonGroup: ({ isMobile: k }) =>
              c(Yi, {
                experience: t,
                onManagePreferencesClick: S,
                enabledKeys: o,
                onSave: (V, R) => {
                  f(V, R), O();
                },
                isAcknowledge: r,
                isMobile: k,
                fidesPreviewMode: e.fidesPreviewMode,
              }),
          }),
        renderModalContent: () =>
          c(
            "div",
            null,
            c(
              "div",
              { className: "fides-modal-notices" },
              c(va, {
                notices: a,
                enabledNoticeKeys: o,
                onChange: (m) => {
                  e.fidesPreviewMode || (d(m), U("FidesUIChanged", i, e.debug));
                },
              })
            )
          ),
        renderModalFooter: ({ onClose: m, isMobile: C }) =>
          c(
            K,
            null,
            c(Yi, {
              experience: t,
              enabledKeys: o,
              onSave: (O, S) => {
                f(O, S), m();
              },
              isInModal: !0,
              isAcknowledge: r,
              isMobile: C,
              saveOnly: a.length === 1,
              fidesPreviewMode: e.fidesPreviewMode,
            }),
            c(Mt, { experience: t.experience_config })
          ),
      });
    };
  var ba = Object.defineProperty,
    Zi = Object.getOwnPropertySymbols,
    _a = Object.prototype.hasOwnProperty,
    ma = Object.prototype.propertyIsEnumerable,
    Xi = (t, e, n) =>
      e in t
        ? ba(t, e, { enumerable: !0, configurable: !0, writable: !0, value: n })
        : (t[e] = n),
    ya = (t, e) => {
      for (var n in e || (e = {})) _a.call(e, n) && Xi(t, n, e[n]);
      if (Zi) for (var n of Zi(e)) ma.call(e, n) && Xi(t, n, e[n]);
      return t;
    };
  const wa = (t, e) => {
    Ei(c(ha, ya({}, t)), e);
  };
  var Ca = (t, e, n) =>
    new Promise((i, s) => {
      var o = (r) => {
          try {
            a(n.next(r));
          } catch (p) {
            s(p);
          }
        },
        d = (r) => {
          try {
            a(n.throw(r));
          } catch (p) {
            s(p);
          }
        },
        a = (r) => (r.done ? i(r.value) : Promise.resolve(r.value).then(o, d));
      a((n = n.apply(t, e)).next());
    });
  function es(t) {
    return Ca(this, null, function* () {
      var e;
      if (!((e = t.options.apiOptions) != null && e.getPreferencesFn))
        return null;
      b(t.options.debug, "Calling custom get preferences fn");
      try {
        return yield t.options.apiOptions.getPreferencesFn(t);
      } catch (n) {
        return (
          b(
            t.options.debug,
            "Error retrieving preferences from custom API, continuing. Error: ",
            n
          ),
          null
        );
      }
    });
  }
  var Ea = Object.defineProperty,
    Ia = Object.defineProperties,
    xa = Object.getOwnPropertyDescriptors,
    ts = Object.getOwnPropertySymbols,
    Oa = Object.prototype.hasOwnProperty,
    Sa = Object.prototype.propertyIsEnumerable,
    ns = (t, e, n) =>
      e in t
        ? Ea(t, e, { enumerable: !0, configurable: !0, writable: !0, value: n })
        : (t[e] = n),
    Ie = (t, e) => {
      for (var n in e || (e = {})) Oa.call(e, n) && ns(t, n, e[n]);
      if (ts) for (var n of ts(e)) Sa.call(e, n) && ns(t, n, e[n]);
      return t;
    },
    is = (t, e) => Ia(t, xa(e)),
    ss = (t, e, n) =>
      new Promise((i, s) => {
        var o = (r) => {
            try {
              a(n.next(r));
            } catch (p) {
              s(p);
            }
          },
          d = (r) => {
            try {
              a(n.throw(r));
            } catch (p) {
              s(p);
            }
          },
          a = (r) =>
            r.done ? i(r.value) : Promise.resolve(r.value).then(o, d);
        a((n = n.apply(t, e)).next());
      });
  let it;
  const Pa = (t, e, n, i) =>
    ss(void 0, null, function* () {
      let s = e;
      const o = Fn(t.consent);
      return i && o && (s = xt({ experience: e, cookie: t, debug: n })), s;
    });
  (it = {
    consent: {},
    experience: void 0,
    geolocation: {},
    options: {
      debug: !0,
      isOverlayEnabled: !1,
      isPrefetchEnabled: !1,
      isGeolocationEnabled: !1,
      geolocationApiUrl: "",
      overlayParentId: null,
      modalLinkId: null,
      privacyCenterUrl: "",
      fidesApiUrl: "",
      serverSideFidesApiUrl: "",
      tcfEnabled: !1,
      fidesEmbed: !1,
      fidesDisableSaveApi: !1,
      fidesDisableBanner: !1,
      fidesString: null,
      apiOptions: null,
      fidesTcfGdprApplies: !1,
      fidesJsBaseUrl: "",
      customOptionsPath: null,
      preventDismissal: !1,
      allowHTMLDescription: null,
      fidesPreviewMode: !1,
    },
    fides_meta: {},
    identity: {},
    tcf_consent: {},
    gtm: Zt,
    init: (t) =>
      ss(void 0, null, function* () {
        var e, n;
        const i = ni(t),
          s = yield es(t),
          o = { optionsOverrides: i, consentPrefsOverrides: s };
        t.options = Ie(Ie({}, t.options), o.optionsOverrides);
        const d = Ie(
            Ie({}, ii(t)),
            (e = o.consentPrefsOverrides) == null ? void 0 : e.consent
          ),
          a = si(
            is(Ie({}, t), { cookie: d, updateExperienceFromCookieConsent: xt })
          );
        a && (Object.assign(it, a), U("FidesInitialized", d, t.options.debug));
        const r = (n = a?.experience) != null ? n : t.experience,
          p = yield oi(
            is(Ie({}, t), {
              cookie: d,
              experience: r,
              renderOverlay: wa,
              updateExperience: ({
                cookie: l,
                experience: f,
                debug: u,
                isExperienceClientSideFetched: g,
              }) => Pa(l, f, u, g),
            })
          );
        Object.assign(it, p), U("FidesInitialized", d, t.options.debug);
      }),
    initialized: !1,
    meta: Xt,
    shopify: tn,
  }),
    typeof window < "u" && (window.Fides = it);
  const ge = (t) => (t ? t.map((e) => `${e.id}`) : []),
    os = ({
      experience: t,
      onManagePreferencesClick: e,
      onSave: n,
      firstButton: i,
      isMobile: s,
      includePrivacyPolicy: o,
    }) => {
      if (!t.experience_config) return null;
      const d = () => {
          const r = {
            purposesConsent: ge(t.tcf_purpose_consents),
            purposesLegint: ge(t.tcf_purpose_legitimate_interests),
            specialPurposes: ge(t.tcf_special_purposes),
            features: ge(t.tcf_features),
            specialFeatures: ge(t.tcf_special_features),
            vendorsConsent: ge([
              ...(t.tcf_vendor_consents || []),
              ...(t.tcf_system_consents || []),
            ]),
            vendorsLegint: ge([
              ...(t.tcf_vendor_legitimate_interests || []),
              ...(t.tcf_system_legitimate_interests || []),
            ]),
          };
          n(G.ACCEPT, r);
        },
        a = () => {
          const r = {
            purposesConsent: [],
            purposesLegint: [],
            specialPurposes: [],
            features: [],
            specialFeatures: [],
            vendorsConsent: [],
            vendorsLegint: [],
          };
          n(G.REJECT, r);
        };
      return c(Ki, {
        experienceConfig: t.experience_config,
        onManagePreferencesClick: e,
        onAcceptAll: d,
        onRejectAll: a,
        firstButton: i,
        isMobile: s,
        includePrivacyPolicy: o,
      });
    },
    Ta = ({ purposeIds: t, specialFeatureIds: e, stacks: n }) => {
      const i = new Set(t),
        s = new Set(e),
        o = Object.entries(n)
          .filter(([, d]) => {
            const a = d.purposes.every((p) => i.has(p)),
              r = d.specialFeatures.every((p) => s.has(p));
            return a && r;
          })
          .map((d) => d[1]);
      return o.filter((d) => {
        const a = d.purposes,
          r = d.specialFeatures,
          p = o.filter((f) => {
            const u = new Set(f.purposes);
            return a.every((g) => u.has(g));
          }),
          l = o.filter((f) => {
            const u = new Set(f.specialFeatures);
            return r.every((g) => u.has(g));
          });
        return !!((a.length && p.length === 1) || (r.length && l.length === 1));
      });
    },
    rs = ({ ids: t, stacks: e, modelType: n }) => {
      const i = new Set([].concat(...e.map((s) => s[n])));
      return t.filter((s) => !i.has(s));
    };
  var ka = Object.defineProperty,
    Aa = Object.defineProperties,
    La = Object.getOwnPropertyDescriptors,
    as = Object.getOwnPropertySymbols,
    Na = Object.prototype.hasOwnProperty,
    $a = Object.prototype.propertyIsEnumerable,
    ds = (t, e, n) =>
      e in t
        ? ka(t, e, { enumerable: !0, configurable: !0, writable: !0, value: n })
        : (t[e] = n),
    ls = (t, e) => {
      for (var n in e || (e = {})) Na.call(e, n) && ds(t, n, e[n]);
      if (as) for (var n of as(e)) $a.call(e, n) && ds(t, n, e[n]);
      return t;
    },
    Fa = (t, e) => Aa(t, La(e));
  const Ra = () =>
      c(
        "svg",
        {
          xmlns: "http://www.w3.org/2000/svg",
          width: "24",
          height: "24",
          fill: "none",
        },
        c("path", {
          fill: "#2D3748",
          d: "m12 13.172 4.95-4.95 1.414 1.414L12 16 5.636 9.636 7.05 8.222l4.95 4.95Z",
        })
      ),
    jt = ({ title: t, description: e, purposes: n }) => {
      const {
        isOpen: i,
        getButtonProps: s,
        getDisclosureProps: o,
        onToggle: d,
      } = Hi({ id: t });
      return c(
        "div",
        {
          className: i
            ? "fides-notice-toggle fides-notice-toggle-expanded"
            : "fides-notice-toggle",
        },
        c(
          "div",
          { key: t, className: "fides-notice-toggle-title" },
          c(
            "span",
            Fa(
              ls(
                {
                  role: "button",
                  tabIndex: 0,
                  onKeyDown: (a) => {
                    (a.code === "Space" || a.code === "Enter") && d();
                  },
                },
                s()
              ),
              { className: "fides-notice-toggle-trigger" }
            ),
            t,
            c(Ra, null)
          )
        ),
        c(
          "div",
          ls({}, o()),
          c("div", null, e),
          n != null && n.length
            ? c(
                "div",
                { className: "fides-tcf-purpose-vendor fides-background-dark" },
                c(
                  "div",
                  {
                    className:
                      "fides-tcf-purpose-vendor-title fides-tcf-toggle-content",
                  },
                  "Purposes include"
                ),
                c(
                  "ul",
                  {
                    className:
                      "fides-tcf-purpose-vendor-list fides-tcf-toggle-content",
                  },
                  n.map((a) => c("li", null, "Purpose ", a.id, ": ", a.name))
                )
              )
            : null
        )
      );
    };
  var Va = Object.defineProperty,
    Da = Object.defineProperties,
    Ua = Object.getOwnPropertyDescriptors,
    cs = Object.getOwnPropertySymbols,
    Ma = Object.prototype.hasOwnProperty,
    ja = Object.prototype.propertyIsEnumerable,
    ps = (t, e, n) =>
      e in t
        ? Va(t, e, { enumerable: !0, configurable: !0, writable: !0, value: n })
        : (t[e] = n),
    Bt = (t, e) => {
      for (var n in e || (e = {})) Ma.call(e, n) && ps(t, n, e[n]);
      if (cs) for (var n of cs(e)) ja.call(e, n) && ps(t, n, e[n]);
      return t;
    },
    Ba = (t, e) => Da(t, Ua(e));
  const us = ({ consentPurposes: t = [], legintPurposes: e = [] }) => {
      const n = Array.from(
          new Set([...t.map((s) => s.id), ...e.map((s) => s.id)])
        ).sort((s, o) => s - o),
        i = [];
      return (
        n.forEach((s) => {
          const o = t.find((a) => a.id === s),
            d = e.find((a) => a.id === s);
          if (o || d) {
            const a = Bt(Bt({}, o), d);
            i.push(Ba(Bt({}, a), { id: s, isConsent: !!o, isLegint: !!d }));
          }
        }),
        { uniquePurposeIds: n, uniquePurposes: i }
      );
    },
    fs = (t, e) => {
      const { legal_bases: n } = t;
      return n ? !!n.find((i) => i === e) : !1;
    },
    Ha = ({ experience: t }) => {
      const {
          tcf_purpose_consents: e = [],
          tcf_purpose_legitimate_interests: n = [],
          tcf_special_features: i = [],
        } = t,
        { uniquePurposeIds: s, uniquePurposes: o } = F(
          () => us({ consentPurposes: e, legintPurposes: n }),
          [e, n]
        ),
        d = F(() => i.map((l) => l.id), [i]),
        a = F(
          () =>
            !t.gvl || Object.keys(t.gvl).length === 0
              ? []
              : Ta({
                  purposeIds: s,
                  specialFeatureIds: d,
                  stacks: t.gvl.stacks,
                }),
          [s, d, t.gvl]
        ),
        r = F(() => {
          const l = rs({ ids: s, stacks: a, modelType: "purposes" });
          return o.filter((f) => l.includes(f.id));
        }, [a, s, o]),
        p = F(() => {
          if (!t.tcf_special_features) return [];
          const l = rs({ ids: d, stacks: a, modelType: "specialFeatures" });
          return t.tcf_special_features.filter((f) => l.indexOf(f.id) !== -1);
        }, [a, d, t.tcf_special_features]);
      return c(
        "div",
        null,
        c(
          "div",
          null,
          a.map((l) => {
            const f = o.filter((u) => l.purposes.indexOf(u.id) !== -1);
            return c(jt, {
              key: l.id,
              title: l.name,
              description: l.description,
              purposes: f,
            });
          })
        ),
        c(
          "div",
          null,
          r.map((l) =>
            c(jt, { key: l.id, title: l.name, description: l.description })
          )
        ),
        c(
          "div",
          null,
          p.map((l) =>
            c(jt, { key: l.id, title: l.name, description: l.description })
          )
        )
      );
    },
    xe = ({
      items: t,
      title: e,
      enabledIds: n,
      renderToggleChild: i,
      renderBadgeLabel: s,
      onToggle: o,
      hideToggles: d,
    }) => {
      if (t.length === 0) return null;
      const a = (r) => {
        const p = `${r.id}`;
        n.indexOf(p) !== -1 ? o(n.filter((l) => l !== p)) : o([...n, p]);
      };
      return c(
        "div",
        { "data-testid": `records-list-${e}` },
        c("div", { className: "fides-record-header" }, e),
        t.map((r) =>
          c(
            Ji,
            {
              dataUse: { key: `${r.id}`, name: r.name },
              onToggle: () => {
                a(r);
              },
              checked: n.indexOf(`${r.id}`) !== -1,
              badge: s ? s(r) : void 0,
              includeToggle: !d,
            },
            i(r)
          )
        )
      );
    },
    gs = ({ active: t, options: e, onChange: n }) => {
      const i = (s) => {
        n(s);
      };
      return c(
        "div",
        { className: "fides-radio-button-group" },
        e.map((s) => {
          const o = s.value === t.value;
          return c(
            "button",
            {
              role: "radio",
              type: "button",
              "aria-checked": o,
              onClick: () => i(s),
              className: "fides-radio-button",
            },
            s.label
          );
        })
      );
    },
    vs = 10,
    za = (t) => {
      const e = [];
      for (let n = 0; n < t.length; n += 10) e.push(t.slice(n, n + 10));
      return e;
    },
    hs = (t) => {
      const [e, n] = j(1),
        i = za(t),
        s = i.length,
        o = e >= s,
        d = e <= 1,
        a = () => {
          o || n(e + 1);
        },
        r = () => {
          d || n(e - 1);
        },
        p = e === 1 ? 1 : (e - 1) * vs + 1,
        l = e === s ? t.length : e * vs;
      return {
        activeChunk: i[e - 1],
        totalPages: i.length,
        nextPage: a,
        previousPage: r,
        disableNext: o,
        disablePrevious: d,
        rangeStart: p,
        rangeEnd: l,
        totalItems: t.length,
      };
    },
    Ga = () =>
      c(
        "svg",
        {
          xmlns: "http://www.w3.org/2000/svg",
          width: "12",
          height: "12",
          fill: "currentColor",
        },
        c("path", {
          d: "m5.914 6 2.475 2.475-.707.707L4.5 6l3.182-3.182.707.707L5.914 6Z",
        })
      ),
    Ka = () =>
      c(
        "svg",
        {
          xmlns: "http://www.w3.org/2000/svg",
          width: "12",
          height: "12",
          fill: "currentColor",
        },
        c("path", {
          d: "M7.086 6 4.61 3.525l.707-.707L8.5 6 5.318 9.182l-.707-.707L7.086 6Z",
        })
      ),
    bs = ({
      nextPage: t,
      previousPage: e,
      rangeStart: n,
      rangeEnd: i,
      disableNext: s,
      disablePrevious: o,
      totalItems: d,
    }) =>
      c(
        "div",
        { className: "fides-paging-buttons" },
        c("span", { className: "fides-paging-info" }, n, "-", i, " of ", d),
        c(
          "div",
          { className: "fides-flex-center" },
          c(
            "button",
            {
              className: "fides-paging-previous-button",
              type: "button",
              onClick: e,
              disabled: o,
              "aria-label": "Previous page",
            },
            c(Ga, null)
          ),
          c(
            "button",
            {
              className: "fides-paging-next-button",
              type: "button",
              onClick: t,
              disabled: s,
              "aria-label": "Next page",
            },
            c(Ka, null)
          )
        )
      );
  var Ya = Object.defineProperty,
    st = Object.getOwnPropertySymbols,
    _s = Object.prototype.hasOwnProperty,
    ms = Object.prototype.propertyIsEnumerable,
    ys = (t, e, n) =>
      e in t
        ? Ya(t, e, { enumerable: !0, configurable: !0, writable: !0, value: n })
        : (t[e] = n),
    qa = (t, e) => {
      for (var n in e || (e = {})) _s.call(e, n) && ys(t, n, e[n]);
      if (st) for (var n of st(e)) ms.call(e, n) && ys(t, n, e[n]);
      return t;
    },
    Wa = (t, e) => {
      var n = {};
      for (var i in t) _s.call(t, i) && e.indexOf(i) < 0 && (n[i] = t[i]);
      if (t != null && st)
        for (var i of st(t)) e.indexOf(i) < 0 && ms.call(t, i) && (n[i] = t[i]);
      return n;
    };
  const ws = ({ vendors: t }) => {
      const e = hs(t),
        { activeChunk: n, totalPages: i } = e,
        s = Wa(e, ["activeChunk", "totalPages"]);
      return n.length
        ? c(
            "p",
            {
              className:
                "fides-tcf-toggle-content fides-background-dark fides-tcf-purpose-vendor",
            },
            c(
              "span",
              { className: "fides-tcf-purpose-vendor-title" },
              "Vendors we use for this purpose",
              c("span", null, t.length, " vendor(s)")
            ),
            c(
              "ul",
              { className: "fides-tcf-purpose-vendor-list" },
              n.map((o) => c("li", null, o.name))
            ),
            i > 1 ? c(bs, qa({}, s)) : null
          )
        : null;
    },
    Cs = ({ purpose: t }) => {
      const e = [...(t.vendors || []), ...(t.systems || [])];
      return c(
        "div",
        null,
        c("p", { className: "fides-tcf-toggle-content" }, t.description),
        t.illustrations.map((n) =>
          c(
            "p",
            { className: "fides-tcf-illustration fides-background-dark" },
            n
          )
        ),
        c(ws, { vendors: e })
      );
    },
    Qa = ({
      allPurposesConsent: t = [],
      allPurposesLegint: e = [],
      allSpecialPurposes: n,
      enabledPurposeConsentIds: i,
      enabledPurposeLegintIds: s,
      enabledSpecialPurposeIds: o,
      onChange: d,
    }) => {
      const { uniquePurposes: a } = F(
          () => us({ consentPurposes: t, legintPurposes: e }),
          [t, e]
        ),
        [r, p] = j(je[0]),
        l = F(() => {
          const f = n ?? [];
          return r.value === te.CONSENT
            ? {
                purposes: a.filter((u) => u.isConsent),
                purposeModelType: "purposesConsent",
                enabledPurposeIds: i,
                specialPurposes: f.filter((u) => fs(u, te.CONSENT)),
                enabledSpecialPurposeIds: o,
              }
            : {
                purposes: a.filter((u) => u.isLegint),
                purposeModelType: "purposesLegint",
                enabledPurposeIds: s,
                specialPurposes: f.filter((u) =>
                  fs(u, te.LEGITIMATE_INTERESTS)
                ),
                enabledSpecialPurposeIds: o,
              };
        }, [r, a, i, s, n, o]);
      return c(
        "div",
        null,
        c(gs, { options: je, active: r, onChange: p }),
        c(xe, {
          title: "Purposes",
          items: l.purposes,
          enabledIds: l.enabledPurposeIds,
          onToggle: (f) =>
            d({ newEnabledIds: f, modelType: l.purposeModelType }),
          renderToggleChild: (f) => c(Cs, { purpose: f }),
          key: `purpose-record-${r.value}`,
        }),
        c(xe, {
          title: "Special purposes",
          items: l.specialPurposes,
          enabledIds: l.enabledSpecialPurposeIds,
          onToggle: (f) =>
            d({ newEnabledIds: f, modelType: "specialPurposes" }),
          renderToggleChild: (f) => c(Cs, { purpose: f }),
          hideToggles: !0,
          key: `special-purpose-record-${r.value}`,
        })
      );
    },
    Es = ({ feature: t }) => {
      const e = [...(t.vendors || []), ...(t.systems || [])];
      return c(
        "div",
        null,
        c("p", { className: "fides-tcf-toggle-content" }, t.description),
        c(ws, { vendors: e })
      );
    },
    Ja = ({
      allFeatures: t,
      allSpecialFeatures: e,
      enabledFeatureIds: n,
      enabledSpecialFeatureIds: i,
      onChange: s,
    }) =>
      c(
        "div",
        null,
        c(xe, {
          title: "Features",
          items: t ?? [],
          enabledIds: n,
          onToggle: (o) => s({ newEnabledIds: o, modelType: "features" }),
          renderToggleChild: (o) => c(Es, { feature: o }),
          hideToggles: !0,
        }),
        c(xe, {
          title: "Special features",
          items: e ?? [],
          enabledIds: i,
          onToggle: (o) =>
            s({ newEnabledIds: o, modelType: "specialFeatures" }),
          renderToggleChild: (o) => c(Es, { feature: o }),
        })
      ),
    Is = ({ href: t, children: e }) =>
      c(
        "a",
        {
          href: t,
          className: "fides-external-link",
          target: "_blank",
          rel: "noopener noreferrer",
        },
        e
      );
  var Za = Object.defineProperty,
    ot = Object.getOwnPropertySymbols,
    xs = Object.prototype.hasOwnProperty,
    Os = Object.prototype.propertyIsEnumerable,
    Ss = (t, e, n) =>
      e in t
        ? Za(t, e, { enumerable: !0, configurable: !0, writable: !0, value: n })
        : (t[e] = n),
    Xa = (t, e) => {
      for (var n in e || (e = {})) xs.call(e, n) && Ss(t, n, e[n]);
      if (ot) for (var n of ot(e)) Os.call(e, n) && Ss(t, n, e[n]);
      return t;
    },
    ed = (t, e) => {
      var n = {};
      for (var i in t) xs.call(t, i) && e.indexOf(i) < 0 && (n[i] = t[i]);
      if (t != null && ot)
        for (var i of ot(t)) e.indexOf(i) < 0 && Os.call(t, i) && (n[i] = t[i]);
      return n;
    };
  const rt = ({ label: t, lineItems: e }) => {
      if (!e || e.length === 0) return null;
      const n = e.some((i) => i.retention_period != null);
      return c(
        "table",
        { className: "fides-vendor-details-table" },
        c(
          "thead",
          null,
          c(
            "tr",
            null,
            c("th", { width: "80%" }, t),
            n
              ? c(
                  "th",
                  { width: "20%", style: { textAlign: "right" } },
                  "Retention"
                )
              : null
          )
        ),
        c(
          "tbody",
          null,
          e.map((i) =>
            c(
              "tr",
              { key: i.id },
              c("td", null, i.name),
              n
                ? c(
                    "td",
                    { style: { textAlign: "right" } },
                    i.retention_period ? `${i.retention_period} day(s)` : "N/A"
                  )
                : null
            )
          )
        )
      );
    },
    td = ({ purposes: t, specialPurposes: e }) => {
      const n = t ? t.length === 0 : !0,
        i = e ? e.length === 0 : !0;
      return n && i
        ? null
        : c(
            K,
            null,
            c(rt, { label: "Purposes", lineItems: t }),
            c(rt, { label: "Special purposes", lineItems: e })
          );
    },
    nd = ({ gvlVendor: t, dataCategories: e }) => {
      if (!t || !e) return null;
      const n = t.dataDeclaration;
      return c(
        "table",
        { className: "fides-vendor-details-table" },
        c("thead", null, c("tr", null, c("th", null, "Data categories"))),
        c(
          "tbody",
          null,
          n?.map((i) => {
            const s = e[i];
            return c("tr", { key: i }, c("td", null, s?.name || ""));
          })
        )
      );
    },
    id = ({ vendor: t }) => {
      const {
        name: e,
        uses_cookies: n,
        uses_non_cookie_access: i,
        cookie_max_age_seconds: s,
        cookie_refresh: o,
      } = t;
      let d = "";
      if (n) {
        const a = s ? Math.ceil(s / 60 / 60 / 24) : 0;
        (d = `${e} stores cookies with a maximum duration of about ${a} Day(s).`),
          o && (d = `${d} These cookies may be refreshed.`),
          i &&
            (d = `${d} This vendor also uses other methods like "local storage" to store and access information on your device.`);
      } else
        i &&
          (d = `${e} uses methods like "local storage" to store and access information on your device.`);
      return d === "" || !d ? null : c("p", null, d);
    },
    Ps = ({ vendor: t, experience: e }) => {
      var n;
      const i = _e(t.id, e.gvl),
        s = (n = e.gvl) == null ? void 0 : n.dataCategories,
        o = t.privacy_policy_url || t.legitimate_interest_disclosure_url;
      return c(
        K,
        null,
        c(id, { vendor: t }),
        o &&
          c(
            "div",
            null,
            t.privacy_policy_url &&
              c(Is, { href: t.privacy_policy_url }, "Privacy policy"),
            t.legitimate_interest_disclosure_url &&
              c(
                Is,
                { href: t.legitimate_interest_disclosure_url },
                "Legitimate interest disclosure"
              )
          ),
        c(td, {
          purposes: [
            ...(t.purpose_consents || []),
            ...(t.purpose_legitimate_interests || []),
          ],
          specialPurposes: t.special_purposes,
        }),
        c(rt, { label: "Features", lineItems: t.features }),
        c(rt, { label: "Special features", lineItems: t.special_features }),
        c(nd, { gvlVendor: i, dataCategories: s })
      );
    },
    sd = ({ experience: t, vendors: e, enabledIds: n, onChange: i }) => {
      const s = hs(e),
        { activeChunk: o, totalPages: d } = s,
        a = ed(s, ["activeChunk", "totalPages"]),
        { gvlVendors: r, otherVendors: p } = F(
          () => ({
            gvlVendors: o.filter((l) => l.isGvl),
            otherVendors: o.filter((l) => !l.isGvl),
          }),
          [o]
        );
      return c(
        K,
        null,
        c(xe, {
          title: "IAB TCF vendors",
          items: r,
          enabledIds: n,
          onToggle: i,
          renderBadgeLabel: (l) => (_e(l.id, t.gvl) ? "IAB TCF" : void 0),
          renderToggleChild: (l) => c(Ps, { vendor: l, experience: t }),
        }),
        c(xe, {
          title: "Other vendors",
          items: p,
          enabledIds: n,
          onToggle: i,
          renderToggleChild: (l) => c(Ps, { vendor: l, experience: t }),
        }),
        c(bs, Xa({}, a))
      );
    },
    od = ({
      experience: t,
      enabledVendorConsentIds: e,
      enabledVendorLegintIds: n,
      onChange: i,
    }) => {
      const s = F(() => wo(t), [t]),
        [o, d] = j(je[0]),
        a = F(() => {
          const r =
            o.value === te.CONSENT
              ? s.filter((p) => p.isConsent)
              : s.filter((p) => p.isLegint);
          return [...r.filter((p) => p.isGvl), ...r.filter((p) => !p.isGvl)];
        }, [o, s]);
      return c(
        "div",
        null,
        c(gs, { options: je, active: o, onChange: d }),
        c(sd, {
          experience: t,
          vendors: a,
          enabledIds: o.value === te.CONSENT ? e : n,
          onChange: (r) =>
            i({
              newEnabledIds: r,
              modelType:
                o.value === te.CONSENT ? "vendorsConsent" : "vendorsLegint",
            }),
          key: `vendor-data-${o.value}`,
        })
      );
    },
    Ht = ({ title: t, children: e }) =>
      c(
        "div",
        { className: "fides-info-box" },
        t ? c("p", { className: "fides-gpc-header" }, t) : null,
        e
      );
  var rd = Object.defineProperty,
    ad = Object.defineProperties,
    dd = Object.getOwnPropertyDescriptors,
    Ts = Object.getOwnPropertySymbols,
    ld = Object.prototype.hasOwnProperty,
    cd = Object.prototype.propertyIsEnumerable,
    ks = (t, e, n) =>
      e in t
        ? rd(t, e, { enumerable: !0, configurable: !0, writable: !0, value: n })
        : (t[e] = n),
    pd = (t, e) => {
      for (var n in e || (e = {})) ld.call(e, n) && ks(t, n, e[n]);
      if (Ts) for (var n of Ts(e)) cd.call(e, n) && ks(t, n, e[n]);
      return t;
    },
    ud = (t, e) => ad(t, dd(e));
  const fd = "ArrowRight",
    gd = "ArrowLeft",
    vd = ({
      experience: t,
      enabledIds: e,
      onChange: n,
      activeTabIndex: i,
      onTabChange: s,
    }) => {
      const o = L(
          ({ newEnabledIds: p, modelType: l }) => {
            const f = ud(pd({}, e), { [l]: p });
            n(f);
          },
          [e, n]
        ),
        d = [
          {
            name: "Purposes",
            content: c(
              "div",
              null,
              c(
                Ht,
                null,
                "Below, you will find a list of the purposes and special features for which your data is being processed. You may exercise your rights for specific purposes, based on consent or legitimate interest, using the toggles below."
              ),
              c(Qa, {
                allPurposesConsent: t.tcf_purpose_consents,
                allPurposesLegint: t.tcf_purpose_legitimate_interests,
                allSpecialPurposes: t.tcf_special_purposes,
                enabledPurposeConsentIds: e.purposesConsent,
                enabledPurposeLegintIds: e.purposesLegint,
                enabledSpecialPurposeIds: e.specialPurposes,
                onChange: o,
              })
            ),
          },
          {
            name: "Features",
            content: c(
              "div",
              null,
              c(
                Ht,
                null,
                "Below, you will find a list of the features for which your data is being processed. You may exercise your rights for special features using the toggles below."
              ),
              c(Ja, {
                allFeatures: t.tcf_features,
                allSpecialFeatures: t.tcf_special_features,
                enabledFeatureIds: e.features,
                enabledSpecialFeatureIds: e.specialFeatures,
                onChange: o,
              })
            ),
          },
          {
            name: "Vendors",
            content: c(
              "div",
              null,
              c(
                Ht,
                null,
                "Below, you will find a list of vendors processing your data and the purposes or features of processing they declare. You may exercise your rights for each vendor based on the legal basis they assert."
              ),
              c(od, {
                experience: t,
                enabledVendorConsentIds: e.vendorsConsent,
                enabledVendorLegintIds: e.vendorsLegint,
                onChange: o,
              })
            ),
          },
        ],
        a = [et(null), et(null), et(null)],
        r = (p) => {
          var l;
          let f;
          p.code === fd &&
            (p.preventDefault(), (f = i === d.length - 1 ? 0 : i + 1)),
            p.code === gd &&
              (p.preventDefault(), (f = i === 0 ? d.length - 1 : i - 1)),
            f != null && (s(f), (l = a[f].current) == null || l.focus());
        };
      return c(
        "div",
        { className: "fides-tabs" },
        c(
          "ul",
          { role: "tablist", className: "fides-tab-list" },
          d.map(({ name: p }, l) =>
            c(
              "li",
              { role: "presentation", key: p },
              c(
                "button",
                {
                  id: `fides-tab-${p}`,
                  "aria-selected": l === i,
                  onClick: () => {
                    s(l);
                  },
                  role: "tab",
                  type: "button",
                  className: "fides-tab-button",
                  tabIndex: l === i ? void 0 : -1,
                  onKeyDown: r,
                  ref: a[l],
                },
                p
              )
            )
          )
        ),
        c(
          "div",
          { className: "tabpanel-container" },
          d.map(({ name: p, content: l }, f) =>
            c(
              "section",
              {
                role: "tabpanel",
                id: `fides-panel-${p}`,
                "aria-labelledby": `fides-tab-${p}`,
                tabIndex: -1,
                hidden: f !== i,
                key: p,
              },
              l
            )
          )
        )
      );
    },
    zt = ({ label: t, count: e, onClick: n }) =>
      c(
        "div",
        { className: "fides-flex-center" },
        n
          ? c(
              "button",
              {
                type: "button",
                className: "fides-link-button fides-vendor-info-label",
                onClick: n,
              },
              t
            )
          : c("span", { className: "fides-vendor-info-label" }, t),
        " ",
        c("span", { className: "fides-notice-badge" }, e.toLocaleString())
      ),
    hd = ({ experience: t, goToVendorTab: e }) => {
      const n = F(() => {
        const {
            tcf_vendor_consents: i = [],
            tcf_vendor_legitimate_interests: s = [],
            tcf_system_consents: o = [],
            tcf_system_legitimate_interests: d = [],
            tcf_vendor_relationships: a = [],
            tcf_system_relationships: r = [],
          } = t,
          p = a.length + r.length,
          l = o.length + i.length,
          f = s.length + d.length;
        return { total: p, consent: l, legint: f };
      }, [t]);
      return c(
        "div",
        { className: "fides-background-dark fides-vendor-info-banner" },
        c(zt, { label: "Vendors", count: n.total, onClick: e }),
        c(zt, { label: "Vendors using consent", count: n.consent }),
        c(zt, { label: "Vendors using legitimate interest", count: n.legint })
      );
    };
  var bd = Object.defineProperty,
    _d = Object.defineProperties,
    md = Object.getOwnPropertyDescriptors,
    As = Object.getOwnPropertySymbols,
    yd = Object.prototype.hasOwnProperty,
    wd = Object.prototype.propertyIsEnumerable,
    Ls = (t, e, n) =>
      e in t
        ? bd(t, e, { enumerable: !0, configurable: !0, writable: !0, value: n })
        : (t[e] = n),
    Ns = (t, e) => {
      for (var n in e || (e = {})) yd.call(e, n) && Ls(t, n, e[n]);
      if (As) for (var n of As(e)) wd.call(e, n) && Ls(t, n, e[n]);
      return t;
    },
    $s = (t, e) => _d(t, md(e)),
    Cd = (t, e, n) =>
      new Promise((i, s) => {
        var o = (r) => {
            try {
              a(n.next(r));
            } catch (p) {
              s(p);
            }
          },
          d = (r) => {
            try {
              a(n.throw(r));
            } catch (p) {
              s(p);
            }
          },
          a = (r) =>
            r.done ? i(r.value) : Promise.resolve(r.value).then(o, d);
        a((n = n.apply(t, e)).next());
      });
  const Ed = (t) =>
      t.current_preference
        ? ye(t.current_preference)
        : ye(t.default_preference),
    ve = (t) =>
      t
        ? t
            .map((e) => {
              const n = Ed(e);
              return $s(Ns({}, e), { consentValue: n });
            })
            .filter((e) => e.consentValue)
            .map((e) => `${e.id}`)
        : [],
    he = ({ modelList: t, enabledIds: e }) =>
      t
        ? t.map((n) => {
            const i = de(e.includes(`${n.id}`));
            return { id: n.id, preference: i };
          })
        : [],
    Id = ({ experience: t, enabledIds: e }) => {
      const { tcf_system_consents: n, tcf_system_legitimate_interests: i } = t,
        s = [],
        o = [],
        d = [],
        a = [];
      return (
        e.vendorsConsent.forEach((r) => {
          n != null && n.map((p) => p.id).includes(r) ? s.push(r) : o.push(r);
        }),
        e.vendorsLegint.forEach((r) => {
          i != null && i.map((p) => p.id).includes(r) ? d.push(r) : a.push(r);
        }),
        {
          purpose_consent_preferences: he({
            modelList: t.tcf_purpose_consents,
            enabledIds: e.purposesConsent,
          }),
          purpose_legitimate_interests_preferences: he({
            modelList: t.tcf_purpose_legitimate_interests,
            enabledIds: e.purposesLegint,
          }),
          special_feature_preferences: he({
            modelList: t.tcf_special_features,
            enabledIds: e.specialFeatures,
          }),
          vendor_consent_preferences: he({
            modelList: t.tcf_vendor_consents,
            enabledIds: o,
          }),
          vendor_legitimate_interests_preferences: he({
            modelList: t.tcf_vendor_legitimate_interests,
            enabledIds: a,
          }),
          system_consent_preferences: he({
            modelList: t.tcf_system_consents,
            enabledIds: s,
          }),
          system_legitimate_interests_preferences: he({
            modelList: t.tcf_system_legitimate_interests,
            enabledIds: d,
          }),
        }
      );
    },
    xd = (t, e, n, i) =>
      Cd(void 0, null, function* () {
        var s;
        const o = yield No({ tcStringPreferences: n, experience: i });
        return $s(Ns({}, t), {
          fides_string: o,
          tcf_consent: jn(e),
          tcf_version_hash: (s = i.meta) == null ? void 0 : s.version_hash,
        });
      }),
    Od = ({ fidesRegionString: t, experience: e, options: n, cookie: i }) => {
      const s = F(() => {
          const {
            tcf_purpose_consents: T = [],
            tcf_purpose_legitimate_interests: m = [],
            tcf_special_purposes: C = [],
            tcf_features: O = [],
            tcf_special_features: S = [],
            tcf_vendor_consents: k = [],
            tcf_vendor_legitimate_interests: V = [],
            tcf_system_consents: R = [],
            tcf_system_legitimate_interests: B = [],
          } = e;
          return {
            purposesConsent: ve(T),
            purposesLegint: ve(m),
            specialPurposes: ve(C),
            features: ve(O),
            specialFeatures: ve(S),
            vendorsConsent: ve([...k, ...R]),
            vendorsLegint: ve([...V, ...B]),
          };
        }, [e]),
        [o, d] = j(s),
        { servedNotice: a } = zi({
          notices: [],
          options: n,
          userGeography: t,
          acknowledgeMode: !1,
          privacyExperience: e,
        }),
        r = L(
          (T, m) => {
            const C = Id({ experience: e, enabledIds: m });
            Pt({
              consentPreferencesToSave: [],
              experience: e,
              consentMethod: T,
              options: n,
              userLocationString: t,
              cookie: i,
              debug: n.debug,
              tcf: C,
              servedNoticeHistoryId: a?.served_notice_history_id,
              updateCookie: (O) => xd(O, C, m, e),
            }),
              d(m);
          },
          [i, e, t, n, a]
        ),
        [p, l] = j(0),
        f = L(() => {
          U("FidesUIShown", i, n.debug, { servingComponent: ue.TCF_BANNER });
        }, [i, n.debug]),
        u = L(() => {
          U("FidesUIShown", i, n.debug, { servingComponent: ue.TCF_OVERLAY });
        }, [i, n.debug]),
        g = L(() => {
          r(G.DISMISS, s);
        }, [r, s]);
      if (!e.experience_config)
        return b(n.debug, "No experience config found"), null;
      const h = e.experience_config;
      return c(Gi, {
        options: n,
        experience: e,
        cookie: i,
        onVendorPageClick: () => {
          l(2);
        },
        onOpen: u,
        onDismiss: g,
        renderBanner: ({
          isOpen: T,
          onClose: m,
          onSave: C,
          onManagePreferencesClick: O,
        }) => {
          const S = () => {
            O(), l(2);
          };
          return c(
            Rt,
            {
              bannerIsOpen: T,
              fidesPreviewMode: n.fidesPreviewMode,
              onOpen: f,
              onClose: () => {
                m(), g();
              },
              experience: h,
              onVendorPageClick: S,
              renderButtonGroup: ({ isMobile: k }) =>
                c(os, {
                  experience: e,
                  onManagePreferencesClick: O,
                  onSave: (V, R) => {
                    r(V, R), C();
                  },
                  isMobile: k,
                  includePrivacyPolicy: !0,
                }),
              className: "fides-tcf-banner-container",
            },
            c(
              "div",
              { id: "fides-tcf-banner-inner" },
              c(hd, { experience: e, goToVendorTab: S }),
              c(Ha, { experience: e })
            )
          );
        },
        renderModalContent: () =>
          c(vd, {
            experience: e,
            enabledIds: o,
            onChange: (T) => {
              d(T), U("FidesUIChanged", i, n.debug);
            },
            activeTabIndex: p,
            onTabChange: l,
          }),
        renderModalFooter: ({ onClose: T, isMobile: m }) => {
          var C;
          const O = (S, k) => {
            r(S, k), T();
          };
          return c(
            K,
            null,
            c(os, {
              experience: e,
              onSave: O,
              firstButton: c(Ee, {
                buttonType: J.SECONDARY,
                label:
                  (C = e.experience_config) == null
                    ? void 0
                    : C.save_button_label,
                onClick: () => O(G.SAVE, o),
                className: "fides-save-button",
              }),
              isMobile: m,
            }),
            c(Mt, { experience: e.experience_config })
          );
        },
      });
    };
  var Sd = Object.defineProperty,
    Fs = Object.getOwnPropertySymbols,
    Pd = Object.prototype.hasOwnProperty,
    Td = Object.prototype.propertyIsEnumerable,
    Rs = (t, e, n) =>
      e in t
        ? Sd(t, e, { enumerable: !0, configurable: !0, writable: !0, value: n })
        : (t[e] = n),
    kd = (t, e) => {
      for (var n in e || (e = {})) Pd.call(e, n) && Rs(t, n, e[n]);
      if (Fs) for (var n of Fs(e)) Td.call(e, n) && Rs(t, n, e[n]);
      return t;
    };
  const Ad = (t, e) => {
      Ei(c(Od, kd({}, t)), e);
    },
    Vs = "__tcfapiLocator",
    Ds = (t) => {
      if (!window.frames[t])
        if (window.document.body) {
          const e = window.document.createElement("iframe");
          (e.style.cssText = "display:none"),
            (e.name = t),
            window.document.body.appendChild(e);
        } else setTimeout(Ds, 5);
    },
    Ld = (t) => {
      let e = window,
        n;
      for (; e; ) {
        try {
          if (e.frames[t]) {
            n = e;
            break;
          }
        } catch {}
        if (e === window.top) break;
        e = e.parent;
      }
      return n;
    },
    Nd = (t) => typeof t == "object" && t != null && "__tcfapiCall" in t,
    $d = ({ gdprAppliesDefault: t = !1 }) => {
      const e = [],
        n = window;
      let i = t;
      function s(...d) {
        return d.length
          ? (d[0] === "setGdprApplies"
              ? d.length > 3 &&
                parseInt(d[1], 10) === 2 &&
                typeof d[3] == "boolean" &&
                ((i = d[3]), typeof d[2] == "function" && d[2]("set", !0))
              : d[0] === "ping"
              ? typeof d[2] == "function" &&
                d[2]({ gdprApplies: i, cmpLoaded: !1, cmpStatus: "stub" })
              : e.push(d),
            null)
          : e;
      }
      function o(d) {
        const a = typeof d.data == "string";
        let r = {};
        if (a)
          try {
            r = JSON.parse(d.data);
          } catch {
            r = {};
          }
        else r = d.data;
        if (!Nd(r)) return null;
        const p = r.__tcfapiCall;
        return (
          p &&
            window.__tcfapi &&
            window.__tcfapi(
              p.command,
              p.version,
              (l, f) => {
                const u = {
                  __tcfapiReturn: {
                    returnValue: l,
                    success: f,
                    callId: p.callId,
                  },
                };
                d &&
                  d.source &&
                  d.source.postMessage &&
                  d.source.postMessage(a ? JSON.stringify(u) : u, "*");
              },
              p.parameter
            ),
          null
        );
      }
      Ld(Vs) ||
        (Ds(Vs), (n.__tcfapi = s), n.addEventListener("message", o, !1));
    },
    Us = (t) => {
      const e = t.split(Me);
      if (e.length === 1) return { tc: e[0], ac: "" };
      if (e.length >= 2) {
        const [n, i] = e;
        return n === "" ? { tc: "", ac: "" } : { tc: n, ac: i };
      }
      return { tc: "", ac: "" };
    },
    Fd = (t, e) => {
      if (!/\d~/.test(t))
        return b(!!e, `Received invalid AC string ${t}, returning no ids`), [];
      const n = t.split("~");
      if (n.length !== 2) return [];
      const i = n[1].split(".");
      return i.length === 1 && i[0] === "" ? [] : i.map((s) => `${rn.AC}.${s}`);
    };
  var Rd = Object.defineProperty,
    Vd = Object.defineProperties,
    Dd = Object.getOwnPropertyDescriptors,
    Ms = Object.getOwnPropertySymbols,
    Ud = Object.prototype.hasOwnProperty,
    Md = Object.prototype.propertyIsEnumerable,
    js = (t, e, n) =>
      e in t
        ? Rd(t, e, { enumerable: !0, configurable: !0, writable: !0, value: n })
        : (t[e] = n),
    at = (t, e) => {
      for (var n in e || (e = {})) Ud.call(e, n) && js(t, n, e[n]);
      if (Ms) for (var n of Ms(e)) Md.call(e, n) && js(t, n, e[n]);
      return t;
    },
    Bs = (t, e) => Vd(t, Dd(e));
  const Hs = (t, e) => {
      const n = {
        tcf_purpose_consents: t.tcf_purpose_consents,
        tcf_purpose_legitimate_interests: t.tcf_purpose_legitimate_interests,
        tcf_special_purposes: t.tcf_special_purposes,
        tcf_features: t.tcf_features,
        tcf_special_features: t.tcf_special_features,
        tcf_vendor_consents: t.tcf_vendor_consents,
        tcf_vendor_legitimate_interests: t.tcf_vendor_legitimate_interests,
        tcf_system_consents: t.tcf_system_consents,
        tcf_system_legitimate_interests: t.tcf_system_legitimate_interests,
      };
      if (
        (cn.forEach(({ cookieKey: i, experienceKey: s }) => {
          var o, d;
          const a = (o = e.tcf_consent[i]) != null ? o : {};
          n[s] =
            (d = t[s]) == null
              ? void 0
              : d.map((r) => {
                  const p = Object.hasOwn(a, r.id)
                    ? de(!!a[r.id], z.OPT_IN)
                    : r.default_preference;
                  return Bs(at({}, r), { current_preference: p });
                });
        }),
        e.fides_string)
      ) {
        const { tc: i, ac: s } = Us(e.fides_string),
          o = Fd(s),
          d = Ve.decode(i);
        ln.forEach(({ experienceKey: a, tcfModelKey: r }) => {
          var p;
          const l = r === "vendorConsents" || r === "vendorLegitimateInterests",
            f = Array.from(d[r])
              .filter(([, u]) => u)
              .map(([u]) => (l ? `gvl.${u}` : u));
          n[a] =
            (p = t[a]) == null
              ? void 0
              : p.map((u) => {
                  let g = !!f.find((h) => h === u.id);
                  return (
                    a === "tcf_vendor_consents" &&
                      o.find((h) => h === u.id) &&
                      (g = !0),
                    Bs(at({}, u), { current_preference: de(g, z.OPT_IN) })
                  );
                });
        });
      }
      return n;
    },
    jd = ({ experience: t, cookie: e, debug: n }) => {
      const i = Hs(t, e);
      return (
        n &&
          b(
            n,
            "Returning updated pre-fetched experience with user consent.",
            t
          ),
        at(at({}, t), i)
      );
    };
  var Bd = Object.defineProperty,
    Hd = Object.defineProperties,
    zd = Object.getOwnPropertyDescriptors,
    zs = Object.getOwnPropertySymbols,
    Gd = Object.prototype.hasOwnProperty,
    Kd = Object.prototype.propertyIsEnumerable,
    Gs = (t, e, n) =>
      e in t
        ? Bd(t, e, { enumerable: !0, configurable: !0, writable: !0, value: n })
        : (t[e] = n),
    Oe = (t, e) => {
      for (var n in e || (e = {})) Gd.call(e, n) && Gs(t, n, e[n]);
      if (zs) for (var n of zs(e)) Kd.call(e, n) && Gs(t, n, e[n]);
      return t;
    },
    Ks = (t, e) => Hd(t, zd(e)),
    Ys = (t, e, n) =>
      new Promise((i, s) => {
        var o = (r) => {
            try {
              a(n.next(r));
            } catch (p) {
              s(p);
            }
          },
          d = (r) => {
            try {
              a(n.throw(r));
            } catch (p) {
              s(p);
            }
          },
          a = (r) =>
            r.done ? i(r.value) : Promise.resolve(r.value).then(o, d);
        a((n = n.apply(t, e)).next());
      });
  let dt;
  const Yd = (t) =>
    Ys(
      void 0,
      [t],
      function* ({
        cookie: e,
        experience: n,
        debug: i = !1,
        isExperienceClientSideFetched: s,
      }) {
        return s && e.fides_string
          ? (b(
              i,
              "Overriding preferences from client-side fetched experience with cookie fides_string consent",
              e.fides_string
            ),
            Hs(n, e))
          : n;
      }
    );
  (dt = {
    consent: {},
    experience: void 0,
    geolocation: {},
    options: {
      debug: !0,
      isOverlayEnabled: !1,
      isPrefetchEnabled: !1,
      isGeolocationEnabled: !1,
      geolocationApiUrl: "",
      overlayParentId: null,
      modalLinkId: null,
      privacyCenterUrl: "",
      fidesApiUrl: "",
      serverSideFidesApiUrl: "",
      tcfEnabled: !0,
      fidesEmbed: !1,
      fidesDisableSaveApi: !1,
      fidesDisableBanner: !1,
      fidesString: null,
      apiOptions: null,
      fidesTcfGdprApplies: !0,
      fidesJsBaseUrl: "",
      customOptionsPath: null,
      preventDismissal: !1,
      allowHTMLDescription: null,
      fidesPreviewMode: !1,
    },
    fides_meta: {},
    identity: {},
    tcf_consent: {},
    gtm: Zt,
    init: (t) =>
      Ys(void 0, null, function* () {
        var e, n, i, s;
        const o = ni(t);
        $d({ gdprAppliesDefault: o?.fidesTcfGdprApplies });
        const d = yield es(t);
        !o.fidesString &&
          d != null &&
          d.fides_string &&
          (o.fidesString = d.fides_string);
        const a = { optionsOverrides: o, consentPrefsOverrides: d };
        t.options = Oe(Oe({}, t.options), a.optionsOverrides);
        const r = Oe(
            Oe({}, ii(t)),
            (e = a.consentPrefsOverrides) == null ? void 0 : e.consent
          ),
          { fidesString: p } = t.options;
        if (p)
          try {
            const { tc: g } = Us(p);
            Ve.decode(g);
            const h = {
              fides_string: p,
              tcf_version_hash:
                (i =
                  (n = a.consentPrefsOverrides) == null
                    ? void 0
                    : n.version_hash) != null
                  ? i
                  : r.tcf_version_hash,
            };
            Object.assign(r, h);
          } catch (g) {
            b(
              t.options.debug,
              `Could not decode tcString from ${p}, it may be invalid. ${g}`
            );
          }
        const l = si(
          Ks(Oe({}, t), { cookie: r, updateExperienceFromCookieConsent: jd })
        );
        $o(),
          l &&
            (Object.assign(dt, l), U("FidesInitialized", r, t.options.debug));
        const f = (s = l?.experience) != null ? s : t.experience,
          u = yield oi(
            Ks(Oe({}, t), {
              cookie: r,
              experience: f,
              renderOverlay: Ad,
              updateExperience: Yd,
            })
          );
        Object.assign(dt, u), U("FidesInitialized", r, t.options.debug);
      }),
    initialized: !1,
    meta: Xt,
    shopify: tn,
  }),
    typeof window < "u" && (window.Fides = dt),
    (y.BannerEnabled = En),
    (y.ButtonType = J),
    (y.CONSENT_COOKIE_MAX_AGE_DAYS = Nn),
    (y.CONSENT_COOKIE_NAME = Et),
    (y.ComponentType = ne),
    (y.ConsentBanner = Rt),
    (y.ConsentMechanism = z),
    (y.ConsentMethod = G),
    (y.EnforcementLevel = Cn),
    (y.GpcStatus = me),
    (y.RequestOrigin = In),
    (y.SaveConsentPreference = ze),
    (y.ServingComponent = ue),
    (y.UserConsentPreference = Q),
    (y.consentCookieObjHasSomeConsentSet = Fn),
    (y.constructFidesRegionString = Ct),
    (y.debugLog = b),
    (y.dispatchFidesEvent = U),
    (y.experienceIsValid = Sn),
    (y.generateFidesUserDeviceId = Rn),
    (y.getConsentContext = ae),
    (y.getCookieByName = It),
    (y.getGpcStatusFromNotice = kn),
    (y.getOrMakeFidesCookie = Un),
    (y.getTcfDefaultPreference = zo),
    (y.getWindowObjFromPath = Tn),
    (y.initOverlay = ei),
    (y.isNewFidesCookie = Vn),
    (y.isPrivacyExperience = we),
    (y.makeConsentDefaultsLegacy = Bn),
    (y.makeFidesCookie = Dn),
    (y.noticeHasConsentInCookie = Ge),
    (y.removeCookiesFromBrowser = Hn),
    (y.resolveConsentValue = wt),
    (y.resolveLegacyConsentValue = xn),
    (y.saveFidesCookie = Mn),
    (y.shouldResurfaceConsent = Pn),
    (y.transformConsentToFidesUserPreference = de),
    (y.transformTcfPreferencesToCookieKeys = jn),
    (y.transformUserPreferenceToBoolean = ye),
    (y.updateCookieFromNoticePreferences = Ot),
    (y.updateExperienceFromCookieConsentNotices = xt),
    (y.validateOptions = On);
});
