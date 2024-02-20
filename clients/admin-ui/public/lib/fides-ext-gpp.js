class ae {
  eventName;
  listenerId;
  data;
  pingData;
  constructor(e, t, n, i) {
    (this.eventName = e),
      (this.listenerId = t),
      (this.data = n),
      (this.pingData = i);
  }
}
class se {
  gppVersion;
  cmpStatus;
  cmpDisplayStatus;
  signalStatus;
  supportedAPIs;
  cmpId;
  sectionList;
  applicableSections;
  gppString;
  parsedSections;
  constructor(e) {
    (this.gppVersion = e.gppVersion),
      (this.cmpStatus = e.cmpStatus),
      (this.cmpDisplayStatus = e.cmpDisplayStatus),
      (this.signalStatus = e.signalStatus),
      (this.supportedAPIs = e.supportedAPIs),
      (this.cmpId = e.cmpId),
      (this.sectionList = e.gppModel.getSectionIds()),
      (this.applicableSections = e.applicableSections),
      (this.gppString = e.gppModel.encode()),
      (this.parsedSections = e.gppModel.toObject());
  }
}
class j {
  callback;
  parameter;
  success = !0;
  cmpApiContext;
  constructor(e, t, n) {
    (this.cmpApiContext = e),
      Object.assign(this, { callback: t, parameter: n });
  }
  execute() {
    try {
      return this.respond();
    } catch {
      return this.invokeCallback(null), null;
    }
  }
  invokeCallback(e) {
    const t = e !== null;
    this.callback && this.callback(e, t);
  }
}
class Ue extends j {
  respond() {
    let e = this.cmpApiContext.eventQueue.add({
        callback: this.callback,
        parameter: this.parameter,
      }),
      t = new ae("listenerRegistered", e, !0, new se(this.cmpApiContext));
    this.invokeCallback(t);
  }
}
class ve extends j {
  respond() {
    let e = new se(this.cmpApiContext);
    this.invokeCallback(e);
  }
}
class be extends j {
  respond() {
    if (!this.parameter || this.parameter.length === 0)
      throw new Error("<section>.<field> parameter required");
    let e = this.parameter.split(".");
    if (e.length != 2)
      throw new Error("Field name must be in the format <section>.<fieldName>");
    let t = e[0],
      n = e[1],
      i = this.cmpApiContext.gppModel.getFieldValue(t, n);
    this.invokeCallback(i);
  }
}
class ye extends j {
  respond() {
    if (!this.parameter || this.parameter.length === 0)
      throw new Error("<section> parameter required");
    let e = null;
    this.cmpApiContext.gppModel.hasSection(this.parameter) &&
      (e = this.cmpApiContext.gppModel.getSection(this.parameter)),
      this.invokeCallback(e);
  }
}
class xe extends j {
  respond() {
    if (!this.parameter || this.parameter.length === 0)
      throw new Error("<section>[.version] parameter required");
    let e = this.cmpApiContext.gppModel.hasSection(this.parameter);
    this.invokeCallback(e);
  }
}
var b;
(function (s) {
  (s.ADD_EVENT_LISTENER = "addEventListener"),
    (s.GET_FIELD = "getField"),
    (s.GET_SECTION = "getSection"),
    (s.HAS_SECTION = "hasSection"),
    (s.PING = "ping"),
    (s.REMOVE_EVENT_LISTENER = "removeEventListener");
})(b || (b = {}));
class Be extends j {
  respond() {
    let e = this.parameter,
      t = this.cmpApiContext.eventQueue.remove(e),
      n = new ae("listenerRemoved", e, t, new se(this.cmpApiContext));
    this.invokeCallback(n);
  }
}
class Te {
  static [b.ADD_EVENT_LISTENER] = Ue;
  static [b.GET_FIELD] = be;
  static [b.GET_SECTION] = ye;
  static [b.HAS_SECTION] = xe;
  static [b.PING] = ve;
  static [b.REMOVE_EVENT_LISTENER] = Be;
}
var Q;
(function (s) {
  (s.STUB = "stub"),
    (s.LOADING = "loading"),
    (s.LOADED = "loaded"),
    (s.ERROR = "error");
})(Q || (Q = {}));
var k;
(function (s) {
  (s.VISIBLE = "visible"), (s.HIDDEN = "hidden"), (s.DISABLED = "disabled");
})(k || (k = {}));
var ue;
(function (s) {
  (s.GPP_LOADED = "gpploaded"),
    (s.CMP_UI_SHOWN = "cmpuishown"),
    (s.USER_ACTION_COMPLETE = "useractioncomplete");
})(ue || (ue = {}));
var B;
(function (s) {
  (s.NOT_READY = "not ready"), (s.READY = "ready");
})(B || (B = {}));
class He {
  callQueue;
  customCommands;
  cmpApiContext;
  constructor(e, t) {
    if (((this.cmpApiContext = e), t)) {
      let n = b.ADD_EVENT_LISTENER;
      if (t?.[n])
        throw new Error(`Built-In Custom Commmand for ${n} not allowed`);
      if (((n = b.REMOVE_EVENT_LISTENER), t?.[n]))
        throw new Error(`Built-In Custom Commmand for ${n} not allowed`);
      this.customCommands = t;
    }
    try {
      this.callQueue = window.__gpp() || [];
    } catch {
      this.callQueue = [];
    } finally {
      (window.__gpp = this.apiCall.bind(this)), this.purgeQueuedCalls();
    }
  }
  apiCall(e, t, n, i) {
    if (typeof e != "string") t(null, !1);
    else {
      if (t && typeof t != "function")
        throw new Error("invalid callback function");
      this.isCustomCommand(e)
        ? this.customCommands[e](t, n)
        : this.isBuiltInCommand(e)
        ? new Te[e](this.cmpApiContext, t, n).execute()
        : t && t(null, !1);
    }
  }
  purgeQueuedCalls() {
    const e = this.callQueue;
    (this.callQueue = []),
      e.forEach((t) => {
        window.__gpp(...t);
      });
  }
  isCustomCommand(e) {
    return this.customCommands && typeof this.customCommands[e] == "function";
  }
  isBuiltInCommand(e) {
    return Te[e] !== void 0;
  }
}
class Fe {
  eventQueue = new Map();
  queueNumber = 1e3;
  cmpApiContext;
  constructor(e) {
    this.cmpApiContext = e;
    try {
      let n = window.__gpp("events") || [];
      for (var t = 0; t < n.length; t++) {
        let i = n[t];
        this.eventQueue.set(i.id, {
          callback: i.callback,
          parameter: i.parameter,
        });
      }
    } catch (n) {
      console.log(n);
    }
  }
  add(e) {
    return this.eventQueue.set(this.queueNumber, e), this.queueNumber++;
  }
  get(e) {
    return this.eventQueue.get(e);
  }
  remove(e) {
    return this.eventQueue.delete(e);
  }
  exec(e, t) {
    this.eventQueue.forEach((n, i) => {
      let r = new ae(e, i, t, new se(this.cmpApiContext)),
        o = !0;
      n.callback(r, o);
    });
  }
  clear() {
    (this.queueNumber = 1e3), this.eventQueue.clear();
  }
  get size() {
    return this.eventQueue.size;
  }
}
class f extends Error {
  constructor(e) {
    super(e), (this.name = "DecodingError");
  }
}
class O {
  static encode(e, t) {
    let n = [];
    if (e >= 1) for (n.push(1); e >= n[0] * 2; ) n.unshift(n[0] * 2);
    let i = "";
    for (let r = 0; r < n.length; r++) {
      let o = n[r];
      e >= o ? ((i += "1"), (e -= o)) : (i += "0");
    }
    for (; i.length < t; ) i = "0" + i;
    return i;
  }
  static decode(e) {
    if (!/^[0-1]*$/.test(e))
      throw new f("Undecodable FixedInteger '" + e + "'");
    let t = 0,
      n = [];
    for (let i = 0; i < e.length; i++)
      i === 0
        ? (n[e.length - (i + 1)] = 1)
        : (n[e.length - (i + 1)] = n[e.length - i] * 2);
    for (let i = 0; i < e.length; i++) e.charAt(i) === "1" && (t += n[i]);
    return t;
  }
}
class ne extends Error {
  constructor(e) {
    super(e), (this.name = "EncodingError");
  }
}
class te {
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
  encode(e) {
    if (!/^[0-1]*$/.test(e)) throw new ne("Unencodable Base64Url '" + e + "'");
    e = this.pad(e);
    let t = "",
      n = 0;
    for (; n <= e.length - 6; ) {
      let i = e.substring(n, n + 6);
      try {
        let r = O.decode(i),
          o = te.DICT.charAt(r);
        (t += o), (n += 6);
      } catch {
        throw new ne("Unencodable Base64Url '" + e + "'");
      }
    }
    return t;
  }
  decode(e) {
    if (!/^[A-Za-z0-9\-_]*$/.test(e))
      throw new f("Undecodable Base64URL string");
    let t = "";
    for (let n = 0; n < e.length; n++) {
      let i = e.charAt(n),
        r = te.REVERSE_DICT.get(i),
        o = O.encode(r, 6);
      t += o;
    }
    return t;
  }
}
class K extends te {
  pad(e) {
    for (; e.length % 8 > 0; ) e += "0";
    for (; e.length % 6 > 0; ) e += "0";
    return e;
  }
}
class X {
  static encode(e) {
    let t = [];
    if (e >= 1 && (t.push(1), e >= 2)) {
      t.push(2);
      let i = 2;
      for (; e >= t[i - 1] + t[i - 2]; ) t.push(t[i - 1] + t[i - 2]), i++;
    }
    let n = "1";
    for (let i = t.length - 1; i >= 0; i--) {
      let r = t[i];
      e >= r ? ((n = "1" + n), (e -= r)) : (n = "0" + n);
    }
    return n;
  }
  static decode(e) {
    if (!/^[0-1]*$/.test(e) || e.length < 2 || e.indexOf("11") !== e.length - 2)
      throw new f("Undecodable FibonacciInteger '" + e + "'");
    let t = 0,
      n = [];
    for (let i = 0; i < e.length - 1; i++)
      i === 0 ? n.push(1) : i === 1 ? n.push(2) : n.push(n[i - 1] + n[i - 2]);
    for (let i = 0; i < e.length - 1; i++) e.charAt(i) === "1" && (t += n[i]);
    return t;
  }
}
class $ {
  static encode(e) {
    if (e === !0) return "1";
    if (e === !1) return "0";
    throw new ne("Unencodable Boolean '" + e + "'");
  }
  static decode(e) {
    if (e === "1") return !0;
    if (e === "0") return !1;
    throw new f("Undecodable Boolean '" + e + "'");
  }
}
class pe {
  static encode(e) {
    e = e.sort((o, S) => o - S);
    let t = [],
      n = 0,
      i = 0;
    for (; i < e.length; ) {
      let o = i;
      for (; o < e.length - 1 && e[o] + 1 === e[o + 1]; ) o++;
      t.push(e.slice(i, o + 1)), (i = o + 1);
    }
    let r = O.encode(t.length, 12);
    for (let o = 0; o < t.length; o++)
      if (t[o].length == 1) {
        let S = t[o][0] - n;
        (n = t[o][0]), (r += "0" + X.encode(S));
      } else {
        let S = t[o][0] - n;
        n = t[o][0];
        let T = t[o][t[o].length - 1] - n;
        (n = t[o][t[o].length - 1]), (r += "1" + X.encode(S) + X.encode(T));
      }
    return r;
  }
  static decode(e) {
    if (!/^[0-1]*$/.test(e) || e.length < 12)
      throw new f("Undecodable FibonacciIntegerRange '" + e + "'");
    let t = [],
      n = O.decode(e.substring(0, 12)),
      i = 0,
      r = 12;
    for (let o = 0; o < n; o++) {
      let S = $.decode(e.substring(r, r + 1));
      if ((r++, S === !0)) {
        let T = e.indexOf("11", r),
          h = X.decode(e.substring(r, T + 2)) + i;
        (i = h), (r = T + 2), (T = e.indexOf("11", r));
        let P = X.decode(e.substring(r, T + 2)) + i;
        (i = P), (r = T + 2);
        for (let I = h; I <= P; I++) t.push(I);
      } else {
        let T = e.indexOf("11", r),
          h = X.decode(e.substring(r, T + 2)) + i;
        (i = h), t.push(h), (r = T + 2);
      }
    }
    return t;
  }
}
class y {
  value;
  hasValue() {
    return this.value !== void 0 && this.value !== null;
  }
  getValue() {
    return this.value;
  }
  setValue(e) {
    this.value = e;
  }
}
class Ye extends y {
  constructor(e) {
    super(), this.setValue(e);
  }
  encode() {
    return pe.encode(this.value);
  }
  decode(e) {
    this.value = pe.decode(e);
  }
  substring(e, t) {
    let n = O.decode(e.substring(t, t + 12)),
      i = t + 12;
    for (let r = 0; r < n; r++)
      e.charAt(i) === "1"
        ? (i = e.indexOf("11", e.indexOf("11", i + 1) + 2) + 2)
        : (i = e.indexOf("11", i + 1) + 2);
    return e.substring(t, i);
  }
  getValue() {
    return [...super.getValue()];
  }
  setValue(e) {
    super.setValue([...new Set(e)].sort((t, n) => t - n));
  }
}
class l extends y {
  bitStringLength;
  constructor(e, t) {
    super(), (this.bitStringLength = e), this.setValue(t);
  }
  encode() {
    return O.encode(this.value, this.bitStringLength);
  }
  decode(e) {
    this.value = O.decode(e);
  }
  substring(e, t) {
    return e.substring(t, t + this.bitStringLength);
  }
}
var W;
(function (s) {
  (s.ID = "Id"), (s.VERSION = "Version"), (s.SECTION_IDS = "SectionIds");
})(W || (W = {}));
class Se {
  fields;
  fieldOrder;
  constructor(e, t) {
    (this.fields = e), (this.fieldOrder = t);
  }
  hasField(e) {
    return this.fields.has(e);
  }
  getFieldValue(e) {
    return this.fields.has(e) ? this.fields.get(e).getValue() : null;
  }
  setFieldValue(e, t) {
    if (this.fields.has(e)) this.fields.get(e).setValue(t);
    else throw new Error(e + " not found");
  }
  getFieldOrder() {
    return this.fieldOrder;
  }
  encodeToBitString() {
    let e = "";
    for (let t = 0; t < this.fieldOrder.length; t++) {
      let n = this.fieldOrder[t];
      if (this.fields.has(n)) {
        let i = this.fields.get(n);
        e += i.encode();
      } else throw new Error("Field not found: '" + n + "'");
    }
    return e;
  }
  decodeFromBitString(e) {
    let t = 0;
    for (let n = 0; n < this.fieldOrder.length; n++) {
      let i = this.fieldOrder[n];
      if (this.fields.has(i)) {
        let r = this.fields.get(i),
          o = r.substring(e, t);
        r.decode(o), (t += o.length);
      } else throw new Error("Field not found: '" + i + "'");
    }
  }
  toObj() {
    let e = {};
    for (let t = 0; t < this.fieldOrder.length; t++) {
      let n = this.fieldOrder[t];
      if (this.fields.has(n)) {
        let r = this.fields.get(n).getValue();
        e[n] = r;
      }
    }
    return e;
  }
}
class F extends Se {
  static ID = 3;
  static VERSION = 1;
  static NAME = "header";
  base64UrlEncoder = new K();
  constructor(e) {
    let t = new Map();
    t.set(W.ID.toString(), new l(6, F.ID)),
      t.set(W.VERSION.toString(), new l(6, F.VERSION)),
      t.set(W.SECTION_IDS.toString(), new Ye([]));
    let n = [W.ID.toString(), W.VERSION.toString(), W.SECTION_IDS.toString()];
    super(t, n), e && e.length > 0 && this.decode(e);
  }
  encode() {
    let e = this.encodeToBitString();
    return this.base64UrlEncoder.encode(e);
  }
  decode(e) {
    let t = this.base64UrlEncoder.decode(e);
    this.decodeFromBitString(t);
  }
  getId() {
    return F.ID;
  }
  getName() {
    return F.NAME;
  }
}
class U extends y {
  constructor(e) {
    super(), this.setValue(e);
  }
  encode() {
    return $.encode(this.value);
  }
  decode(e) {
    this.value = $.decode(e);
  }
  substring(e, t) {
    return e.substring(t, t + 1);
  }
}
class Oe {
  static encode(e) {
    return e ? O.encode(Math.round(e.getTime() / 100), 36) : O.encode(0, 36);
  }
  static decode(e) {
    if (!/^[0-1]*$/.test(e) || e.length !== 36)
      throw new f("Undecodable Datetime '" + e + "'");
    return new Date(O.decode(e) * 100);
  }
}
class ie extends y {
  constructor(e) {
    super(), this.setValue(e);
  }
  encode() {
    return Oe.encode(this.value);
  }
  decode(e) {
    this.value = Oe.decode(e);
  }
  substring(e, t) {
    return e.substring(t, t + 36);
  }
}
class q {
  static encode(e, t) {
    let n = "";
    for (let i = 0; i < e.length; i++) n += $.encode(e[i]);
    for (; n.length < t; ) n += "0";
    return n;
  }
  static decode(e) {
    if (!/^[0-1]*$/.test(e))
      throw new f("Undecodable FixedBitfield '" + e + "'");
    let t = [];
    for (let n = 0; n < e.length; n++) t.push($.decode(e.substring(n, n + 1)));
    return t;
  }
}
class re extends y {
  getLength;
  constructor(e, t) {
    super(), (this.getLength = e), this.setValue(t);
  }
  encode() {
    return q.encode(this.value, this.getLength());
  }
  decode(e) {
    this.value = q.decode(e);
  }
  substring(e, t) {
    return e.substring(t, t + this.getLength());
  }
  getValue() {
    return [...super.getValue()];
  }
  setValue(e) {
    let t = this.getLength(),
      n = [...e];
    for (let i = n.length; i < t; i++) n.push(!1);
    n.length > t && (n = n.slice(0, t)), super.setValue([...n]);
  }
}
class x extends y {
  numElements;
  constructor(e) {
    super(), (this.numElements = e.length), this.setValue(e);
  }
  encode() {
    return q.encode(this.value, this.numElements);
  }
  decode(e) {
    this.value = q.decode(e);
  }
  substring(e, t) {
    return e.substring(t, t + this.numElements);
  }
  getValue() {
    return [...super.getValue()];
  }
  setValue(e) {
    let t = [...e];
    for (let n = t.length; n < this.numElements; n++) t.push(!1);
    t.length > this.numElements && (t = t.slice(0, this.numElements)),
      super.setValue(t);
  }
}
class he {
  static encode(e, t) {
    for (; e.length < t; ) e += " ";
    let n = "";
    for (let i = 0; i < e.length; i++) {
      let r = e.charCodeAt(i);
      if (r === 32) n += O.encode(63, 6);
      else if (r >= 65) n += O.encode(e.charCodeAt(i) - 65, 6);
      else throw new ne("Unencodable FixedString '" + e + "'");
    }
    return n;
  }
  static decode(e) {
    if (!/^[0-1]*$/.test(e) || e.length % 6 !== 0)
      throw new f("Undecodable FixedString '" + e + "'");
    let t = "";
    for (let n = 0; n < e.length; n += 6) {
      let i = O.decode(e.substring(n, n + 6));
      i === 63 ? (t += " ") : (t += String.fromCharCode(i + 65));
    }
    return t.trim();
  }
}
class Ee extends y {
  stringLength;
  constructor(e, t) {
    super(), (this.stringLength = e), this.setValue(t);
  }
  encode() {
    return he.encode(this.value, this.stringLength);
  }
  decode(e) {
    this.value = he.decode(e);
  }
  substring(e, t) {
    return e.substring(t, t + this.stringLength * 6);
  }
}
class z {
  fields;
  segments;
  constructor(e, t) {
    (this.fields = e), (this.segments = t);
  }
  hasField(e) {
    return this.fields.has(e);
  }
  getFieldValue(e) {
    return this.fields.has(e) ? this.fields.get(e).getValue() : null;
  }
  setFieldValue(e, t) {
    if (this.fields.has(e)) this.fields.get(e).setValue(t);
    else throw new Error(e + " not found");
  }
  getSegments() {
    return this.segments;
  }
  encodeSegmentsToBitStrings() {
    let e = [];
    for (let t = 0; t < this.segments.length; t++) {
      let n = "";
      for (let i = 0; i < this.segments[t].length; i++) {
        let r = this.segments[t][i];
        if (this.fields.has(r))
          try {
            let o = this.fields.get(r);
            n += o.encode();
          } catch {
            throw new Error("Unable to encode " + r);
          }
        else throw new Error("Field not found: '" + r + "'");
      }
      e.push(n);
    }
    return e;
  }
  decodeSegmentsFromBitStrings(e) {
    for (let t = 0; t < this.segments.length && t < e.length; t++) {
      let n = e[t];
      if (n && n.length > 0) {
        let i = 0;
        for (let r = 0; r < this.segments[t].length; r++) {
          let o = this.segments[t][r];
          if (this.fields.has(o))
            try {
              let S = this.fields.get(o),
                T = S.substring(n, i);
              S.decode(T), (i += T.length);
            } catch {
              throw new Error("Unable to decode " + o);
            }
          else throw new Error("Field not found: '" + o + "'");
        }
      }
    }
  }
  toObj() {
    let e = {};
    for (let t = 0; t < this.segments.length; t++)
      for (let n = 0; n < this.segments[t].length; n++) {
        let i = this.segments[t][n];
        if (this.fields.has(i)) {
          let o = this.fields.get(i).getValue();
          e[i] = o;
        }
      }
    return e;
  }
}
class oe {
  static encode(e) {
    e.sort((r, o) => r - o);
    let t = [],
      n = 0;
    for (; n < e.length; ) {
      let r = n;
      for (; r < e.length - 1 && e[r] + 1 === e[r + 1]; ) r++;
      t.push(e.slice(n, r + 1)), (n = r + 1);
    }
    let i = O.encode(t.length, 12);
    for (let r = 0; r < t.length; r++)
      t[r].length === 1
        ? (i += "0" + O.encode(t[r][0], 16))
        : (i +=
            "1" + O.encode(t[r][0], 16) + O.encode(t[r][t[r].length - 1], 16));
    return i;
  }
  static decode(e) {
    if (!/^[0-1]*$/.test(e) || e.length < 12)
      throw new f("Undecodable FixedIntegerRange '" + e + "'");
    let t = [],
      n = O.decode(e.substring(0, 12)),
      i = 12;
    for (let r = 0; r < n; r++) {
      let o = $.decode(e.substring(i, i + 1));
      if ((i++, o === !0)) {
        let S = O.decode(e.substring(i, i + 16));
        i += 16;
        let T = O.decode(e.substring(i, i + 16));
        i += 16;
        for (let h = S; h <= T; h++) t.push(h);
      } else {
        let S = O.decode(e.substring(i, i + 16));
        t.push(S), (i += 16);
      }
    }
    return t;
  }
}
class Ie extends y {
  constructor(e) {
    super(), this.setValue(e);
  }
  encode() {
    return oe.encode(this.value);
  }
  decode(e) {
    this.value = oe.decode(e);
  }
  substring(e, t) {
    let n = O.decode(e.substring(t, t + 12)),
      i = t + 12;
    for (let r = 0; r < n; r++) e.charAt(i) === "1" ? (i += 33) : (i += 17);
    return e.substring(t, i);
  }
  getValue() {
    return [...super.getValue()];
  }
  setValue(e) {
    super.setValue([...new Set(e)].sort((t, n) => t - n));
  }
}
class J extends y {
  constructor(e) {
    super(), this.setValue(e);
  }
  encode() {
    let e = this.value.length > 0 ? this.value[this.value.length - 1] : 0,
      t = oe.encode(this.value),
      n = t.length,
      i = e;
    if (n <= i) return O.encode(e, 16) + "1" + t;
    {
      let r = [],
        o = 0;
      for (let S = 0; S < e; S++)
        S === this.value[o] - 1 ? ((r[S] = !0), o++) : (r[S] = !1);
      return O.encode(e, 16) + "0" + q.encode(r, i);
    }
  }
  decode(e) {
    if (e.charAt(16) === "1") this.value = oe.decode(e.substring(17));
    else {
      let t = [],
        n = q.decode(e.substring(17));
      for (let i = 0; i < n.length; i++) n[i] === !0 && t.push(i + 1);
      this.value = t;
    }
  }
  substring(e, t) {
    let n = O.decode(e.substring(t, t + 16));
    return e.charAt(t + 16) === "1"
      ? e.substring(t, t + 17) + new Ie([]).substring(e, t + 17)
      : e.substring(t, t + 17 + n);
  }
  getValue() {
    return [...super.getValue()];
  }
  setValue(e) {
    super.setValue([...new Set(e)].sort((t, n) => t - n));
  }
}
var a;
(function (s) {
  (s.VERSION = "Version"),
    (s.CREATED = "Created"),
    (s.LAST_UPDATED = "LastUpdated"),
    (s.CMP_ID = "CmpId"),
    (s.CMP_VERSION = "CmpVersion"),
    (s.CONSENT_SCREEN = "ConsentScreen"),
    (s.CONSENT_LANGUAGE = "ConsentLanguage"),
    (s.VENDOR_LIST_VERSION = "VendorListVersion"),
    (s.POLICY_VERSION = "PolicyVersion"),
    (s.IS_SERVICE_SPECIFIC = "IsServiceSpecific"),
    (s.USE_NON_STANDARD_STACKS = "UseNonStandardStacks"),
    (s.SPECIAL_FEATURE_OPTINS = "SpecialFeatureOptins"),
    (s.PURPOSE_CONSENTS = "PurposeConsents"),
    (s.PURPOSE_LEGITIMATE_INTERESTS = "PurposeLegitimateInterests"),
    (s.PURPOSE_ONE_TREATMENT = "PurposeOneTreatment"),
    (s.PUBLISHER_COUNTRY_CODE = "PublisherCountryCode"),
    (s.VENDOR_CONSENTS = "VendorConsents"),
    (s.VENDOR_LEGITIMATE_INTERESTS = "VendorLegitimateInterests"),
    (s.PUBLISHER_RESTRICTIONS = "PublisherRestrictions"),
    (s.PUBLISHER_PURPOSES_SEGMENT_TYPE = "PublisherPurposesSegmentType"),
    (s.PUBLISHER_CONSENTS = "PublisherConsents"),
    (s.PUBLISHER_LEGITIMATE_INTERESTS = "PublisherLegitimateInterests"),
    (s.NUM_CUSTOM_PURPOSES = "NumCustomPurposes"),
    (s.PUBLISHER_CUSTOM_CONSENTS = "PublisherCustomConsents"),
    (s.PUBLISHER_CUSTOM_LEGITIMATE_INTERESTS =
      "PublisherCustomLegitimateInterests"),
    (s.VENDORS_ALLOWED_SEGMENT_TYPE = "VendorsAllowedSegmentType"),
    (s.VENDORS_ALLOWED = "VendorsAllowed"),
    (s.VENDORS_DISCLOSED_SEGMENT_TYPE = "VendorsDisclosedSegmentType"),
    (s.VENDORS_DISCLOSED = "VendorsDisclosed");
})(a || (a = {}));
class ke extends te {
  pad(e) {
    for (; e.length % 24 > 0; ) e += "0";
    return e;
  }
}
class N extends z {
  static ID = 2;
  static VERSION = 2;
  static NAME = "tcfeuv2";
  base64UrlEncoder = new ke();
  constructor(e) {
    let t = new Map(),
      n = new Date();
    t.set(a.VERSION.toString(), new l(6, N.VERSION)),
      t.set(a.CREATED.toString(), new ie(n)),
      t.set(a.LAST_UPDATED.toString(), new ie(n)),
      t.set(a.CMP_ID.toString(), new l(12, 0)),
      t.set(a.CMP_VERSION.toString(), new l(12, 0)),
      t.set(a.CONSENT_SCREEN.toString(), new l(6, 0)),
      t.set(a.CONSENT_LANGUAGE.toString(), new Ee(2, "EN")),
      t.set(a.VENDOR_LIST_VERSION.toString(), new l(12, 0)),
      t.set(a.POLICY_VERSION.toString(), new l(6, 2)),
      t.set(a.IS_SERVICE_SPECIFIC.toString(), new U(!1)),
      t.set(a.USE_NON_STANDARD_STACKS.toString(), new U(!1)),
      t.set(
        a.SPECIAL_FEATURE_OPTINS.toString(),
        new x([!1, !1, !1, !1, !1, !1, !1, !1, !1, !1, !1, !1])
      ),
      t.set(
        a.PURPOSE_CONSENTS.toString(),
        new x([
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
        ])
      ),
      t.set(
        a.PURPOSE_LEGITIMATE_INTERESTS.toString(),
        new x([
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
        ])
      ),
      t.set(a.PURPOSE_ONE_TREATMENT.toString(), new U(!1)),
      t.set(a.PUBLISHER_COUNTRY_CODE.toString(), new Ee(2, "AA")),
      t.set(a.VENDOR_CONSENTS.toString(), new J([])),
      t.set(a.VENDOR_LEGITIMATE_INTERESTS.toString(), new J([])),
      t.set(a.PUBLISHER_RESTRICTIONS.toString(), new Ie([])),
      t.set(a.PUBLISHER_PURPOSES_SEGMENT_TYPE.toString(), new l(3, 3)),
      t.set(
        a.PUBLISHER_CONSENTS.toString(),
        new x([
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
        ])
      ),
      t.set(
        a.PUBLISHER_LEGITIMATE_INTERESTS.toString(),
        new x([
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
        ])
      );
    let i = new l(6, 0);
    t.set(a.NUM_CUSTOM_PURPOSES.toString(), i),
      t.set(
        a.PUBLISHER_CUSTOM_CONSENTS.toString(),
        new re(() => i.getValue(), [])
      ),
      t.set(
        a.PUBLISHER_CUSTOM_LEGITIMATE_INTERESTS.toString(),
        new re(() => i.getValue(), [])
      ),
      t.set(a.VENDORS_ALLOWED_SEGMENT_TYPE.toString(), new l(3, 2)),
      t.set(a.VENDORS_ALLOWED.toString(), new J([])),
      t.set(a.VENDORS_DISCLOSED_SEGMENT_TYPE.toString(), new l(3, 1)),
      t.set(a.VENDORS_DISCLOSED.toString(), new J([]));
    let r = [
        a.VERSION.toString(),
        a.CREATED.toString(),
        a.LAST_UPDATED.toString(),
        a.CMP_ID.toString(),
        a.CMP_VERSION.toString(),
        a.CONSENT_SCREEN.toString(),
        a.CONSENT_LANGUAGE.toString(),
        a.VENDOR_LIST_VERSION.toString(),
        a.POLICY_VERSION.toString(),
        a.IS_SERVICE_SPECIFIC.toString(),
        a.USE_NON_STANDARD_STACKS.toString(),
        a.SPECIAL_FEATURE_OPTINS.toString(),
        a.PURPOSE_CONSENTS.toString(),
        a.PURPOSE_LEGITIMATE_INTERESTS.toString(),
        a.PURPOSE_ONE_TREATMENT.toString(),
        a.PUBLISHER_COUNTRY_CODE.toString(),
        a.VENDOR_CONSENTS.toString(),
        a.VENDOR_LEGITIMATE_INTERESTS.toString(),
        a.PUBLISHER_RESTRICTIONS.toString(),
      ],
      o = [
        a.PUBLISHER_PURPOSES_SEGMENT_TYPE.toString(),
        a.PUBLISHER_CONSENTS.toString(),
        a.PUBLISHER_LEGITIMATE_INTERESTS.toString(),
        a.NUM_CUSTOM_PURPOSES.toString(),
        a.PUBLISHER_CUSTOM_CONSENTS.toString(),
        a.PUBLISHER_CUSTOM_LEGITIMATE_INTERESTS.toString(),
      ],
      S = [
        a.VENDORS_ALLOWED_SEGMENT_TYPE.toString(),
        a.VENDORS_ALLOWED.toString(),
      ],
      T = [
        a.VENDORS_DISCLOSED_SEGMENT_TYPE.toString(),
        a.VENDORS_DISCLOSED.toString(),
      ],
      h = [r, o, S, T];
    super(t, h), e && e.length > 0 && this.decode(e);
  }
  encode() {
    let e = this.encodeSegmentsToBitStrings(),
      t = [];
    return (
      t.push(this.base64UrlEncoder.encode(e[0])),
      this.getFieldValue(a.IS_SERVICE_SPECIFIC.toString())
        ? e[1] && e[1].length > 0 && t.push(this.base64UrlEncoder.encode(e[1]))
        : (e[2] &&
            e[2].length > 0 &&
            t.push(this.base64UrlEncoder.encode(e[2])),
          e[3] &&
            e[3].length > 0 &&
            t.push(this.base64UrlEncoder.encode(e[3]))),
      t.join(".")
    );
  }
  decode(e) {
    let t = e.split("."),
      n = [];
    for (let i = 0; i < t.length; i++) {
      let r = this.base64UrlEncoder.decode(t[i]);
      switch (r.substring(0, 3)) {
        case "000": {
          n[0] = r;
          break;
        }
        case "001": {
          n[3] = r;
          break;
        }
        case "010": {
          n[2] = r;
          break;
        }
        case "011": {
          n[1] = r;
          break;
        }
        default:
          throw new f("Unable to decode segment '" + t[i] + "'");
      }
    }
    this.decodeSegmentsFromBitStrings(n);
  }
  setFieldValue(e, t) {
    if (
      (super.setFieldValue(e, t),
      e !== a.CREATED.toString() && e !== a.LAST_UPDATED.toString())
    ) {
      const n = new Date(),
        i = new Date(
          Date.UTC(n.getUTCFullYear(), n.getUTCMonth(), n.getUTCDate())
        );
      this.setFieldValue(a.CREATED.toString(), i),
        this.setFieldValue(a.LAST_UPDATED.toString(), i);
    }
  }
  getId() {
    return N.ID;
  }
  getName() {
    return N.NAME;
  }
}
var _;
(function (s) {
  (s.VERSION = "Version"),
    (s.CREATED = "Created"),
    (s.LAST_UPDATED = "LastUpdated"),
    (s.CMP_ID = "CmpId"),
    (s.CMP_VERSION = "CmpVersion"),
    (s.CONSENT_SCREEN = "ConsentScreen"),
    (s.CONSENT_LANGUAGE = "ConsentLanguage"),
    (s.VENDOR_LIST_VERSION = "VendorListVersion"),
    (s.TCF_POLICY_VERSION = "TcfPolicyVersion"),
    (s.USE_NON_STANDARD_STACKS = "UseNonStandardStacks"),
    (s.SPECIAL_FEATURE_EXPRESS_CONSENT = "SpecialFeatureExpressConsent"),
    (s.PURPOSES_EXPRESS_CONSENT = "PurposesExpressConsent"),
    (s.PURPOSES_IMPLIED_CONSENT = "PurposesImpliedConsent"),
    (s.VENDOR_EXPRESS_CONSENT = "VendorExpressConsent"),
    (s.VENDOR_IMPLIED_CONSENT = "VendorImpliedConsent"),
    (s.SEGMENT_TYPE = "SegmentType"),
    (s.PUB_PURPOSES_EXPRESS_CONSENT = "PubPurposesExpressConsent"),
    (s.PUB_PURPOSES_IMPLIED_CONSENT = "PubPurposesImpliedConsent"),
    (s.NUM_CUSTOM_PURPOSES = "NumCustomPurposes"),
    (s.CUSTOM_PURPOSES_EXPRESS_CONSENT = "CustomPurposesExpressConsent"),
    (s.CUSTOM_PURPOSES_IMPLIED_CONSENT = "CustomPurposesImpliedConsent");
})(_ || (_ = {}));
class L extends z {
  static ID = 5;
  static VERSION = 2;
  static NAME = "tcfcav1";
  base64UrlEncoder = new K();
  constructor(e) {
    let t = new Map(),
      n = new Date();
    t.set(_.VERSION.toString(), new l(6, L.VERSION)),
      t.set(_.CREATED.toString(), new ie(n)),
      t.set(_.LAST_UPDATED.toString(), new ie(n)),
      t.set(_.CMP_ID.toString(), new l(12, 0)),
      t.set(_.CMP_VERSION.toString(), new l(12, 0)),
      t.set(_.CONSENT_SCREEN.toString(), new l(6, 0)),
      t.set(_.CONSENT_LANGUAGE.toString(), new Ee(2, "EN")),
      t.set(_.VENDOR_LIST_VERSION.toString(), new l(12, 0)),
      t.set(_.TCF_POLICY_VERSION.toString(), new l(6, 1)),
      t.set(_.USE_NON_STANDARD_STACKS.toString(), new U(!1)),
      t.set(
        _.SPECIAL_FEATURE_EXPRESS_CONSENT.toString(),
        new x([!1, !1, !1, !1, !1, !1, !1, !1, !1, !1, !1, !1])
      ),
      t.set(
        _.PURPOSES_EXPRESS_CONSENT.toString(),
        new x([
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
        ])
      ),
      t.set(
        _.PURPOSES_IMPLIED_CONSENT.toString(),
        new x([
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
        ])
      ),
      t.set(_.VENDOR_EXPRESS_CONSENT.toString(), new J([])),
      t.set(_.VENDOR_IMPLIED_CONSENT.toString(), new J([])),
      t.set(_.SEGMENT_TYPE.toString(), new l(3, 3)),
      t.set(
        _.PUB_PURPOSES_EXPRESS_CONSENT.toString(),
        new x([
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
        ])
      ),
      t.set(
        _.PUB_PURPOSES_IMPLIED_CONSENT.toString(),
        new x([
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
          !1,
        ])
      );
    let i = new l(6, 0);
    t.set(_.NUM_CUSTOM_PURPOSES.toString(), i),
      t.set(
        _.CUSTOM_PURPOSES_EXPRESS_CONSENT.toString(),
        new re(() => i.getValue(), [])
      ),
      t.set(
        _.CUSTOM_PURPOSES_IMPLIED_CONSENT.toString(),
        new re(() => i.getValue(), [])
      );
    let r = [
        _.VERSION.toString(),
        _.CREATED.toString(),
        _.LAST_UPDATED.toString(),
        _.CMP_ID.toString(),
        _.CMP_VERSION.toString(),
        _.CONSENT_SCREEN.toString(),
        _.CONSENT_LANGUAGE.toString(),
        _.VENDOR_LIST_VERSION.toString(),
        _.TCF_POLICY_VERSION.toString(),
        _.USE_NON_STANDARD_STACKS.toString(),
        _.SPECIAL_FEATURE_EXPRESS_CONSENT.toString(),
        _.PURPOSES_EXPRESS_CONSENT.toString(),
        _.PURPOSES_IMPLIED_CONSENT.toString(),
        _.VENDOR_EXPRESS_CONSENT.toString(),
        _.VENDOR_IMPLIED_CONSENT.toString(),
      ],
      o = [
        _.SEGMENT_TYPE.toString(),
        _.PUB_PURPOSES_EXPRESS_CONSENT.toString(),
        _.PUB_PURPOSES_IMPLIED_CONSENT.toString(),
        _.NUM_CUSTOM_PURPOSES.toString(),
        _.CUSTOM_PURPOSES_EXPRESS_CONSENT.toString(),
        _.CUSTOM_PURPOSES_IMPLIED_CONSENT.toString(),
      ],
      S = [r, o];
    super(t, S), e && e.length > 0 && this.decode(e);
  }
  encode() {
    let e = this.encodeSegmentsToBitStrings(),
      t = [];
    return (
      t.push(this.base64UrlEncoder.encode(e[0])),
      e[1] && e[1].length > 0 && t.push(this.base64UrlEncoder.encode(e[1])),
      t.join(".")
    );
  }
  decode(e) {
    let t = e.split("."),
      n = [];
    for (let i = 0; i < t.length; i++) {
      let r = this.base64UrlEncoder.decode(t[i]);
      switch (r.substring(0, 3)) {
        case "000": {
          n[0] = r;
          break;
        }
        case "011": {
          n[1] = r;
          break;
        }
        default:
          throw new f("Unable to decode segment '" + t[i] + "'");
      }
    }
    this.decodeSegmentsFromBitStrings(n);
  }
  setFieldValue(e, t) {
    if (
      (super.setFieldValue(e, t),
      e !== _.CREATED.toString() && e !== _.LAST_UPDATED.toString())
    ) {
      const n = new Date(),
        i = new Date(
          Date.UTC(n.getUTCFullYear(), n.getUTCMonth(), n.getUTCDate())
        );
      this.setFieldValue(_.CREATED.toString(), i),
        this.setFieldValue(_.LAST_UPDATED.toString(), i);
    }
  }
  getId() {
    return L.ID;
  }
  getName() {
    return L.NAME;
  }
}
class Ne extends Error {
  constructor(e) {
    super(e), (this.name = "InvalidFieldError");
  }
}
var G;
(function (s) {
  (s.VERSION = "Version"),
    (s.NOTICE = "Notice"),
    (s.OPT_OUT_SALE = "OptOutSale"),
    (s.LSPA_COVERED = "LspaCovered");
})(G || (G = {}));
class V {
  static ID = 6;
  static VERSION = 1;
  static NAME = "uspv1";
  fields;
  constructor(e) {
    (this.fields = new Map()),
      this.fields.set(G.VERSION.toString(), V.VERSION),
      this.fields.set(G.NOTICE.toString(), "-"),
      this.fields.set(G.OPT_OUT_SALE.toString(), "-"),
      this.fields.set(G.LSPA_COVERED.toString(), "-"),
      e && e.length > 0 && this.decode(e);
  }
  hasField(e) {
    return this.fields.has(e);
  }
  getFieldValue(e) {
    return this.fields.has(e) ? this.fields.get(e) : null;
  }
  setFieldValue(e, t) {
    if (this.fields.has(e)) this.fields.set(e, t);
    else throw new Ne(e + " not found");
  }
  toObj() {
    let e = {};
    for (const t of this.fields.keys()) {
      let n = this.fields.get(t);
      e[t.toString()] = n;
    }
    return e;
  }
  encode() {
    let e = "";
    return (
      (e += this.getFieldValue(G.VERSION.toString())),
      (e += this.getFieldValue(G.NOTICE.toString())),
      (e += this.getFieldValue(G.OPT_OUT_SALE.toString())),
      (e += this.getFieldValue(G.LSPA_COVERED.toString())),
      e
    );
  }
  decode(e) {
    this.setFieldValue(G.VERSION.toString(), parseInt(e.charAt(0))),
      this.setFieldValue(G.NOTICE.toString(), e.charAt(1)),
      this.setFieldValue(G.OPT_OUT_SALE.toString(), e.charAt(2)),
      this.setFieldValue(G.LSPA_COVERED.toString(), e.charAt(3));
  }
  getId() {
    return V.ID;
  }
  getName() {
    return V.NAME;
  }
}
class Ae {
  static encode(e, t, n) {
    let i = "";
    for (let r = 0; r < e.length; r++) i += O.encode(e[r], t);
    for (; i.length < t * n; ) i += "0";
    return i;
  }
  static decode(e, t, n) {
    if (!/^[0-1]*$/.test(e))
      throw new f("Undecodable FixedInteger '" + e + "'");
    if (e.length > t * n)
      throw new f("Undecodable FixedIntegerList '" + e + "'");
    if (e.length % t != 0)
      throw new f("Undecodable FixedIntegerList '" + e + "'");
    for (; e.length < t * n; ) e += "0";
    e.length > t * n && (e = e.substring(0, t * n));
    let i = [];
    for (let r = 0; r < e.length; r += t)
      i.push(O.decode(e.substring(r, r + t)));
    for (; i.length < n; ) i.push(0);
    return i;
  }
}
class H extends y {
  elementBitStringLength;
  numElements;
  constructor(e, t) {
    super(),
      (this.elementBitStringLength = e),
      (this.numElements = t.length),
      this.setValue(t);
  }
  encode() {
    return Ae.encode(this.value, this.elementBitStringLength, this.numElements);
  }
  decode(e) {
    this.value = Ae.decode(e, this.elementBitStringLength, this.numElements);
  }
  substring(e, t) {
    return e.substring(t, t + this.elementBitStringLength * this.numElements);
  }
  getValue() {
    return [...super.getValue()];
  }
  setValue(e) {
    let t = [...e];
    for (let n = t.length; n < this.numElements; n++) t.push(0);
    t.length > this.numElements && (t = t.slice(0, this.numElements)),
      super.setValue(t);
  }
}
var E;
(function (s) {
  (s.VERSION = "Version"),
    (s.SHARING_NOTICE = "SharingNotice"),
    (s.SALE_OPT_OUT_NOTICE = "SaleOptOutNotice"),
    (s.SHARING_OPT_OUT_NOTICE = "SharingOptOutNotice"),
    (s.TARGETED_ADVERTISING_OPT_OUT_NOTICE = "TargetedAdvertisingOptOutNotice"),
    (s.SENSITIVE_DATA_PROCESSING_OPT_OUT_NOTICE =
      "SensitiveDataProcessingOptOutNotice"),
    (s.SENSITIVE_DATA_LIMIT_USE_NOTICE = "SensitiveDataLimitUseNotice"),
    (s.SALE_OPT_OUT = "SaleOptOut"),
    (s.SHARING_OPT_OUT = "SharingOptOut"),
    (s.TARGETED_ADVERTISING_OPT_OUT = "TargetedAdvertisingOptOut"),
    (s.SENSITIVE_DATA_PROCESSING = "SensitiveDataProcessing"),
    (s.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS = "KnownChildSensitiveDataConsents"),
    (s.PERSONAL_DATA_CONSENTS = "PersonalDataConsents"),
    (s.MSPA_COVERED_TRANSACTION = "MspaCoveredTransaction"),
    (s.MSPA_OPT_OUT_OPTION_MODE = "MspaOptOutOptionMode"),
    (s.MSPA_SERVICE_PROVIDER_MODE = "MspaServiceProviderMode"),
    (s.GPC_SEGMENT_TYPE = "GpcSegmentType"),
    (s.GPC_SEGMENT_INCLUDED = "GpcSegmentIncluded"),
    (s.GPC = "Gpc");
})(E || (E = {}));
class C extends z {
  static ID = 7;
  static VERSION = 1;
  static NAME = "usnatv1";
  base64UrlEncoder = new K();
  constructor(e) {
    let t = new Map();
    t.set(E.VERSION.toString(), new l(6, C.VERSION)),
      t.set(E.SHARING_NOTICE.toString(), new l(2, 0)),
      t.set(E.SALE_OPT_OUT_NOTICE.toString(), new l(2, 0)),
      t.set(E.SHARING_OPT_OUT_NOTICE.toString(), new l(2, 0)),
      t.set(E.TARGETED_ADVERTISING_OPT_OUT_NOTICE.toString(), new l(2, 0)),
      t.set(E.SENSITIVE_DATA_PROCESSING_OPT_OUT_NOTICE.toString(), new l(2, 0)),
      t.set(E.SENSITIVE_DATA_LIMIT_USE_NOTICE.toString(), new l(2, 0)),
      t.set(E.SALE_OPT_OUT.toString(), new l(2, 0)),
      t.set(E.SHARING_OPT_OUT.toString(), new l(2, 0)),
      t.set(E.TARGETED_ADVERTISING_OPT_OUT.toString(), new l(2, 0)),
      t.set(
        E.SENSITIVE_DATA_PROCESSING.toString(),
        new H(2, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
      ),
      t.set(E.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS.toString(), new H(2, [0, 0])),
      t.set(E.PERSONAL_DATA_CONSENTS.toString(), new l(2, 0)),
      t.set(E.MSPA_COVERED_TRANSACTION.toString(), new l(2, 0)),
      t.set(E.MSPA_OPT_OUT_OPTION_MODE.toString(), new l(2, 0)),
      t.set(E.MSPA_SERVICE_PROVIDER_MODE.toString(), new l(2, 0)),
      t.set(E.GPC_SEGMENT_TYPE.toString(), new l(2, 1)),
      t.set(E.GPC_SEGMENT_INCLUDED.toString(), new U(!0)),
      t.set(E.GPC.toString(), new U(!1));
    let n = [
        E.VERSION.toString(),
        E.SHARING_NOTICE.toString(),
        E.SALE_OPT_OUT_NOTICE.toString(),
        E.SHARING_OPT_OUT_NOTICE.toString(),
        E.TARGETED_ADVERTISING_OPT_OUT_NOTICE.toString(),
        E.SENSITIVE_DATA_PROCESSING_OPT_OUT_NOTICE.toString(),
        E.SENSITIVE_DATA_LIMIT_USE_NOTICE.toString(),
        E.SALE_OPT_OUT.toString(),
        E.SHARING_OPT_OUT.toString(),
        E.TARGETED_ADVERTISING_OPT_OUT.toString(),
        E.SENSITIVE_DATA_PROCESSING.toString(),
        E.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS.toString(),
        E.PERSONAL_DATA_CONSENTS.toString(),
        E.MSPA_COVERED_TRANSACTION.toString(),
        E.MSPA_OPT_OUT_OPTION_MODE.toString(),
        E.MSPA_SERVICE_PROVIDER_MODE.toString(),
      ],
      i = [E.GPC_SEGMENT_TYPE.toString(), E.GPC.toString()],
      r = [n, i];
    super(t, r), e && e.length > 0 && this.decode(e);
  }
  encode() {
    let e = this.encodeSegmentsToBitStrings(),
      t = [];
    return (
      t.push(this.base64UrlEncoder.encode(e[0])),
      e[1] &&
        e[1].length > 0 &&
        this.fields.get(E.GPC_SEGMENT_INCLUDED).getValue() === !0 &&
        t.push(this.base64UrlEncoder.encode(e[1])),
      t.join(".")
    );
  }
  decode(e) {
    let t = e.split("."),
      n = [],
      i = !1;
    for (let r = 0; r < t.length; r++) {
      let o = this.base64UrlEncoder.decode(t[r]);
      switch (o.substring(0, 2)) {
        case "00": {
          n[0] = o;
          break;
        }
        case "01": {
          (i = !0), (n[1] = o);
          break;
        }
        default:
          throw new f("Unable to decode segment '" + t[r] + "'");
      }
    }
    this.decodeSegmentsFromBitStrings(n),
      this.fields.get(E.GPC_SEGMENT_INCLUDED).setValue(i);
  }
  getId() {
    return C.ID;
  }
  getName() {
    return C.NAME;
  }
}
var c;
(function (s) {
  (s.VERSION = "Version"),
    (s.SALE_OPT_OUT_NOTICE = "SaleOptOutNotice"),
    (s.SHARING_OPT_OUT_NOTICE = "SharingOptOutNotice"),
    (s.SENSITIVE_DATA_LIMIT_USE_NOTICE = "SensitiveDataLimitUseNotice"),
    (s.SALE_OPT_OUT = "SaleOptOut"),
    (s.SHARING_OPT_OUT = "SharingOptOut"),
    (s.SENSITIVE_DATA_PROCESSING = "SensitiveDataProcessing"),
    (s.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS = "KnownChildSensitiveDataConsents"),
    (s.PERSONAL_DATA_CONSENTS = "PersonalDataConsents"),
    (s.MSPA_COVERED_TRANSACTION = "MspaCoveredTransaction"),
    (s.MSPA_OPT_OUT_OPTION_MODE = "MspaOptOutOptionMode"),
    (s.MSPA_SERVICE_PROVIDER_MODE = "MspaServiceProviderMode"),
    (s.GPC_SEGMENT_TYPE = "GpcSegmentType"),
    (s.GPC_SEGMENT_INCLUDED = "GpcSegmentIncluded"),
    (s.GPC = "Gpc");
})(c || (c = {}));
class D extends z {
  static ID = 8;
  static VERSION = 1;
  static NAME = "uscav1";
  base64UrlEncoder = new K();
  constructor(e) {
    let t = new Map();
    t.set(c.VERSION.toString(), new l(6, D.VERSION)),
      t.set(c.SALE_OPT_OUT_NOTICE.toString(), new l(2, 0)),
      t.set(c.SHARING_OPT_OUT_NOTICE.toString(), new l(2, 0)),
      t.set(c.SENSITIVE_DATA_LIMIT_USE_NOTICE.toString(), new l(2, 0)),
      t.set(c.SALE_OPT_OUT.toString(), new l(2, 0)),
      t.set(c.SHARING_OPT_OUT.toString(), new l(2, 0)),
      t.set(
        c.SENSITIVE_DATA_PROCESSING.toString(),
        new H(2, [0, 0, 0, 0, 0, 0, 0, 0, 0])
      ),
      t.set(c.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS.toString(), new H(2, [0, 0])),
      t.set(c.PERSONAL_DATA_CONSENTS.toString(), new l(2, 0)),
      t.set(c.MSPA_COVERED_TRANSACTION.toString(), new l(2, 0)),
      t.set(c.MSPA_OPT_OUT_OPTION_MODE.toString(), new l(2, 0)),
      t.set(c.MSPA_SERVICE_PROVIDER_MODE.toString(), new l(2, 0)),
      t.set(c.GPC_SEGMENT_TYPE.toString(), new l(2, 1)),
      t.set(c.GPC_SEGMENT_INCLUDED.toString(), new U(!0)),
      t.set(c.GPC.toString(), new U(!1));
    let n = [
        c.VERSION.toString(),
        c.SALE_OPT_OUT_NOTICE.toString(),
        c.SHARING_OPT_OUT_NOTICE.toString(),
        c.SENSITIVE_DATA_LIMIT_USE_NOTICE.toString(),
        c.SALE_OPT_OUT.toString(),
        c.SHARING_OPT_OUT.toString(),
        c.SENSITIVE_DATA_PROCESSING.toString(),
        c.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS.toString(),
        c.PERSONAL_DATA_CONSENTS.toString(),
        c.MSPA_COVERED_TRANSACTION.toString(),
        c.MSPA_OPT_OUT_OPTION_MODE.toString(),
        c.MSPA_SERVICE_PROVIDER_MODE.toString(),
      ],
      i = [c.GPC_SEGMENT_TYPE.toString(), c.GPC.toString()],
      r = [n, i];
    super(t, r), e && e.length > 0 && this.decode(e);
  }
  encode() {
    let e = this.encodeSegmentsToBitStrings(),
      t = [];
    return (
      t.push(this.base64UrlEncoder.encode(e[0])),
      e[1] &&
        e[1].length > 0 &&
        this.fields.get(c.GPC_SEGMENT_INCLUDED).getValue() === !0 &&
        t.push(this.base64UrlEncoder.encode(e[1])),
      t.join(".")
    );
  }
  decode(e) {
    let t = e.split("."),
      n = [],
      i = !1;
    for (let r = 0; r < t.length; r++) {
      let o = this.base64UrlEncoder.decode(t[r]);
      switch (o.substring(0, 2)) {
        case "00": {
          n[0] = o;
          break;
        }
        case "01": {
          (i = !0), (n[1] = o);
          break;
        }
        default:
          throw new f("Unable to decode segment '" + t[r] + "'");
      }
    }
    this.decodeSegmentsFromBitStrings(n),
      this.fields.get(c.GPC_SEGMENT_INCLUDED).setValue(i);
  }
  getId() {
    return D.ID;
  }
  getName() {
    return D.NAME;
  }
}
var p;
(function (s) {
  (s.VERSION = "Version"),
    (s.SHARING_NOTICE = "SharingNotice"),
    (s.SALE_OPT_OUT_NOTICE = "SaleOptOutNotice"),
    (s.TARGETED_ADVERTISING_OPT_OUT_NOTICE = "TargetedAdvertisingOptOutNotice"),
    (s.SALE_OPT_OUT = "SaleOptOut"),
    (s.TARGETED_ADVERTISING_OPT_OUT = "TargetedAdvertisingOptOut"),
    (s.SENSITIVE_DATA_PROCESSING = "SensitiveDataProcessing"),
    (s.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS = "KnownChildSensitiveDataConsents"),
    (s.MSPA_COVERED_TRANSACTION = "MspaCoveredTransaction"),
    (s.MSPA_OPT_OUT_OPTION_MODE = "MspaOptOutOptionMode"),
    (s.MSPA_SERVICE_PROVIDER_MODE = "MspaServiceProviderMode");
})(p || (p = {}));
class R extends Se {
  static ID = 9;
  static VERSION = 1;
  static NAME = "usvav1";
  base64UrlEncoder = new K();
  constructor(e) {
    let t = new Map();
    t.set(p.VERSION.toString(), new l(6, R.VERSION)),
      t.set(p.SHARING_NOTICE.toString(), new l(2, 0)),
      t.set(p.SALE_OPT_OUT_NOTICE.toString(), new l(2, 0)),
      t.set(p.TARGETED_ADVERTISING_OPT_OUT_NOTICE.toString(), new l(2, 0)),
      t.set(p.SALE_OPT_OUT.toString(), new l(2, 0)),
      t.set(p.TARGETED_ADVERTISING_OPT_OUT.toString(), new l(2, 0)),
      t.set(
        p.SENSITIVE_DATA_PROCESSING.toString(),
        new H(2, [0, 0, 0, 0, 0, 0, 0, 0])
      ),
      t.set(p.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS.toString(), new l(2, 0)),
      t.set(p.MSPA_COVERED_TRANSACTION.toString(), new l(2, 0)),
      t.set(p.MSPA_OPT_OUT_OPTION_MODE.toString(), new l(2, 0)),
      t.set(p.MSPA_SERVICE_PROVIDER_MODE.toString(), new l(2, 0));
    let n = [
      p.VERSION.toString(),
      p.SHARING_NOTICE.toString(),
      p.SALE_OPT_OUT_NOTICE.toString(),
      p.TARGETED_ADVERTISING_OPT_OUT_NOTICE.toString(),
      p.SALE_OPT_OUT.toString(),
      p.TARGETED_ADVERTISING_OPT_OUT.toString(),
      p.SENSITIVE_DATA_PROCESSING.toString(),
      p.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS.toString(),
      p.MSPA_COVERED_TRANSACTION.toString(),
      p.MSPA_OPT_OUT_OPTION_MODE.toString(),
      p.MSPA_SERVICE_PROVIDER_MODE.toString(),
    ];
    super(t, n), e && e.length > 0 && this.decode(e);
  }
  encode() {
    return this.base64UrlEncoder.encode(this.encodeToBitString());
  }
  decode(e) {
    this.decodeFromBitString(this.base64UrlEncoder.decode(e));
  }
  getId() {
    return R.ID;
  }
  getName() {
    return R.NAME;
  }
}
var d;
(function (s) {
  (s.VERSION = "Version"),
    (s.SHARING_NOTICE = "SharingNotice"),
    (s.SALE_OPT_OUT_NOTICE = "SaleOptOutNotice"),
    (s.TARGETED_ADVERTISING_OPT_OUT_NOTICE = "TargetedAdvertisingOptOutNotice"),
    (s.SALE_OPT_OUT = "SaleOptOut"),
    (s.TARGETED_ADVERTISING_OPT_OUT = "TargetedAdvertisingOptOut"),
    (s.SENSITIVE_DATA_PROCESSING = "SensitiveDataProcessing"),
    (s.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS = "KnownChildSensitiveDataConsents"),
    (s.MSPA_COVERED_TRANSACTION = "MspaCoveredTransaction"),
    (s.MSPA_OPT_OUT_OPTION_MODE = "MspaOptOutOptionMode"),
    (s.MSPA_SERVICE_PROVIDER_MODE = "MspaServiceProviderMode"),
    (s.GPC_SEGMENT_TYPE = "GpcSegmentType"),
    (s.GPC_SEGMENT_INCLUDED = "GpcSegmentIncluded"),
    (s.GPC = "Gpc");
})(d || (d = {}));
class m extends z {
  static ID = 10;
  static VERSION = 1;
  static NAME = "uscov1";
  base64UrlEncoder = new K();
  constructor(e) {
    let t = new Map();
    t.set(d.VERSION.toString(), new l(6, m.VERSION)),
      t.set(d.SHARING_NOTICE.toString(), new l(2, 0)),
      t.set(d.SALE_OPT_OUT_NOTICE.toString(), new l(2, 0)),
      t.set(d.TARGETED_ADVERTISING_OPT_OUT_NOTICE.toString(), new l(2, 0)),
      t.set(d.SALE_OPT_OUT.toString(), new l(2, 0)),
      t.set(d.TARGETED_ADVERTISING_OPT_OUT.toString(), new l(2, 0)),
      t.set(
        d.SENSITIVE_DATA_PROCESSING.toString(),
        new H(2, [0, 0, 0, 0, 0, 0, 0])
      ),
      t.set(d.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS.toString(), new l(2, 0)),
      t.set(d.MSPA_COVERED_TRANSACTION.toString(), new l(2, 0)),
      t.set(d.MSPA_OPT_OUT_OPTION_MODE.toString(), new l(2, 0)),
      t.set(d.MSPA_SERVICE_PROVIDER_MODE.toString(), new l(2, 0)),
      t.set(d.GPC_SEGMENT_TYPE.toString(), new l(2, 1)),
      t.set(d.GPC_SEGMENT_INCLUDED.toString(), new U(!0)),
      t.set(d.GPC.toString(), new U(!1));
    let n = [
        d.VERSION.toString(),
        d.SHARING_NOTICE.toString(),
        d.SALE_OPT_OUT_NOTICE.toString(),
        d.TARGETED_ADVERTISING_OPT_OUT_NOTICE.toString(),
        d.SALE_OPT_OUT.toString(),
        d.TARGETED_ADVERTISING_OPT_OUT.toString(),
        d.SENSITIVE_DATA_PROCESSING.toString(),
        d.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS.toString(),
        d.MSPA_COVERED_TRANSACTION.toString(),
        d.MSPA_OPT_OUT_OPTION_MODE.toString(),
        d.MSPA_SERVICE_PROVIDER_MODE.toString(),
      ],
      i = [d.GPC_SEGMENT_TYPE.toString(), d.GPC.toString()],
      r = [n, i];
    super(t, r), e && e.length > 0 && this.decode(e);
  }
  encode() {
    let e = this.encodeSegmentsToBitStrings(),
      t = [];
    return (
      t.push(this.base64UrlEncoder.encode(e[0])),
      e[1] &&
        e[1].length > 0 &&
        this.fields.get(d.GPC_SEGMENT_INCLUDED).getValue() === !0 &&
        t.push(this.base64UrlEncoder.encode(e[1])),
      t.join(".")
    );
  }
  decode(e) {
    let t = e.split("."),
      n = [],
      i = !1;
    for (let r = 0; r < t.length; r++) {
      let o = this.base64UrlEncoder.decode(t[r]);
      switch (o.substring(0, 2)) {
        case "00": {
          n[0] = o;
          break;
        }
        case "01": {
          (i = !0), (n[1] = o);
          break;
        }
        default:
          throw new f("Unable to decode segment '" + t[r] + "'");
      }
    }
    this.decodeSegmentsFromBitStrings(n),
      this.fields.get(d.GPC_SEGMENT_INCLUDED).setValue(i);
  }
  getId() {
    return m.ID;
  }
  getName() {
    return m.NAME;
  }
}
var u;
(function (s) {
  (s.VERSION = "Version"),
    (s.SHARING_NOTICE = "SharingNotice"),
    (s.SALE_OPT_OUT_NOTICE = "SaleOptOutNotice"),
    (s.TARGETED_ADVERTISING_OPT_OUT_NOTICE = "TargetedAdvertisingOptOutNotice"),
    (s.SENSITIVE_DATA_PROCESSING_OPT_OUT_NOTICE =
      "SensitiveDataProcessingOptOutNotice"),
    (s.SALE_OPT_OUT = "SaleOptOut"),
    (s.TARGETED_ADVERTISING_OPT_OUT = "TargetedAdvertisingOptOut"),
    (s.SENSITIVE_DATA_PROCESSING = "SensitiveDataProcessing"),
    (s.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS = "KnownChildSensitiveDataConsents"),
    (s.MSPA_COVERED_TRANSACTION = "MspaCoveredTransaction"),
    (s.MSPA_OPT_OUT_OPTION_MODE = "MspaOptOutOptionMode"),
    (s.MSPA_SERVICE_PROVIDER_MODE = "MspaServiceProviderMode");
})(u || (u = {}));
class w extends Se {
  static ID = 11;
  static VERSION = 1;
  static NAME = "usutv1";
  base64UrlEncoder = new K();
  constructor(e) {
    let t = new Map();
    t.set(u.VERSION.toString(), new l(6, w.VERSION)),
      t.set(u.SHARING_NOTICE.toString(), new l(2, 0)),
      t.set(u.SALE_OPT_OUT_NOTICE.toString(), new l(2, 0)),
      t.set(u.TARGETED_ADVERTISING_OPT_OUT_NOTICE.toString(), new l(2, 0)),
      t.set(u.SENSITIVE_DATA_PROCESSING_OPT_OUT_NOTICE.toString(), new l(2, 0)),
      t.set(u.SALE_OPT_OUT.toString(), new l(2, 0)),
      t.set(u.TARGETED_ADVERTISING_OPT_OUT.toString(), new l(2, 0)),
      t.set(
        u.SENSITIVE_DATA_PROCESSING.toString(),
        new H(2, [0, 0, 0, 0, 0, 0, 0, 0])
      ),
      t.set(u.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS.toString(), new l(2, 0)),
      t.set(u.MSPA_COVERED_TRANSACTION.toString(), new l(2, 0)),
      t.set(u.MSPA_OPT_OUT_OPTION_MODE.toString(), new l(2, 0)),
      t.set(u.MSPA_SERVICE_PROVIDER_MODE.toString(), new l(2, 0));
    let n = [
      u.VERSION.toString(),
      u.SHARING_NOTICE.toString(),
      u.SALE_OPT_OUT_NOTICE.toString(),
      u.TARGETED_ADVERTISING_OPT_OUT_NOTICE.toString(),
      u.SENSITIVE_DATA_PROCESSING_OPT_OUT_NOTICE.toString(),
      u.SALE_OPT_OUT.toString(),
      u.TARGETED_ADVERTISING_OPT_OUT.toString(),
      u.SENSITIVE_DATA_PROCESSING.toString(),
      u.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS.toString(),
      u.MSPA_COVERED_TRANSACTION.toString(),
      u.MSPA_OPT_OUT_OPTION_MODE.toString(),
      u.MSPA_SERVICE_PROVIDER_MODE.toString(),
    ];
    super(t, n), e && e.length > 0 && this.decode(e);
  }
  encode() {
    return this.base64UrlEncoder.encode(this.encodeToBitString());
  }
  decode(e) {
    this.decodeFromBitString(this.base64UrlEncoder.decode(e));
  }
  getId() {
    return w.ID;
  }
  getName() {
    return w.NAME;
  }
}
var g;
(function (s) {
  (s.VERSION = "Version"),
    (s.SHARING_NOTICE = "SharingNotice"),
    (s.SALE_OPT_OUT_NOTICE = "SaleOptOutNotice"),
    (s.TARGETED_ADVERTISING_OPT_OUT_NOTICE = "TargetedAdvertisingOptOutNotice"),
    (s.SALE_OPT_OUT = "SaleOptOut"),
    (s.TARGETED_ADVERTISING_OPT_OUT = "TargetedAdvertisingOptOut"),
    (s.SENSITIVE_DATA_PROCESSING = "SensitiveDataProcessing"),
    (s.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS = "KnownChildSensitiveDataConsents"),
    (s.MSPA_COVERED_TRANSACTION = "MspaCoveredTransaction"),
    (s.MSPA_OPT_OUT_OPTION_MODE = "MspaOptOutOptionMode"),
    (s.MSPA_SERVICE_PROVIDER_MODE = "MspaServiceProviderMode"),
    (s.GPC_SEGMENT_TYPE = "GpcSegmentType"),
    (s.GPC_SEGMENT_INCLUDED = "GpcSegmentIncluded"),
    (s.GPC = "Gpc");
})(g || (g = {}));
class M extends z {
  static ID = 12;
  static VERSION = 1;
  static NAME = "usctv1";
  base64UrlEncoder = new K();
  constructor(e) {
    let t = new Map();
    t.set(g.VERSION.toString(), new l(6, M.VERSION)),
      t.set(g.SHARING_NOTICE.toString(), new l(2, 0)),
      t.set(g.SALE_OPT_OUT_NOTICE.toString(), new l(2, 0)),
      t.set(g.TARGETED_ADVERTISING_OPT_OUT_NOTICE.toString(), new l(2, 0)),
      t.set(g.SALE_OPT_OUT.toString(), new l(2, 0)),
      t.set(g.TARGETED_ADVERTISING_OPT_OUT.toString(), new l(2, 0)),
      t.set(
        g.SENSITIVE_DATA_PROCESSING.toString(),
        new H(2, [0, 0, 0, 0, 0, 0, 0, 0])
      ),
      t.set(
        g.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS.toString(),
        new H(2, [0, 0, 0])
      ),
      t.set(g.MSPA_COVERED_TRANSACTION.toString(), new l(2, 0)),
      t.set(g.MSPA_OPT_OUT_OPTION_MODE.toString(), new l(2, 0)),
      t.set(g.MSPA_SERVICE_PROVIDER_MODE.toString(), new l(2, 0)),
      t.set(g.GPC_SEGMENT_TYPE.toString(), new l(2, 1)),
      t.set(g.GPC_SEGMENT_INCLUDED.toString(), new U(!0)),
      t.set(g.GPC.toString(), new U(!1));
    let n = [
        g.VERSION.toString(),
        g.SHARING_NOTICE.toString(),
        g.SALE_OPT_OUT_NOTICE.toString(),
        g.TARGETED_ADVERTISING_OPT_OUT_NOTICE.toString(),
        g.SALE_OPT_OUT.toString(),
        g.TARGETED_ADVERTISING_OPT_OUT.toString(),
        g.SENSITIVE_DATA_PROCESSING.toString(),
        g.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS.toString(),
        g.MSPA_COVERED_TRANSACTION.toString(),
        g.MSPA_OPT_OUT_OPTION_MODE.toString(),
        g.MSPA_SERVICE_PROVIDER_MODE.toString(),
      ],
      i = [g.GPC_SEGMENT_TYPE.toString(), g.GPC.toString()],
      r = [n, i];
    super(t, r), e && e.length > 0 && this.decode(e);
  }
  encode() {
    let e = this.encodeSegmentsToBitStrings(),
      t = [];
    return (
      t.push(this.base64UrlEncoder.encode(e[0])),
      e[1] &&
        e[1].length > 0 &&
        this.fields.get(g.GPC_SEGMENT_INCLUDED).getValue() === !0 &&
        t.push(this.base64UrlEncoder.encode(e[1])),
      t.join(".")
    );
  }
  decode(e) {
    let t = e.split("."),
      n = [],
      i = !1;
    for (let r = 0; r < t.length; r++) {
      let o = this.base64UrlEncoder.decode(t[r]);
      switch (o.substring(0, 2)) {
        case "00": {
          n[0] = o;
          break;
        }
        case "01": {
          (i = !0), (n[1] = o);
          break;
        }
        default:
          throw new f("Unable to decode segment '" + t[r] + "'");
      }
    }
    this.decodeSegmentsFromBitStrings(n),
      this.fields.get(g.GPC_SEGMENT_INCLUDED).setValue(i);
  }
  getId() {
    return M.ID;
  }
  getName() {
    return M.NAME;
  }
}
class A {
  static SECTION_ID_NAME_MAP = new Map([
    [N.ID, N.NAME],
    [L.ID, L.NAME],
    [V.ID, V.NAME],
    [C.ID, C.NAME],
    [D.ID, D.NAME],
    [R.ID, R.NAME],
    [m.ID, m.NAME],
    [w.ID, w.NAME],
    [M.ID, M.NAME],
  ]);
  static SECTION_ORDER = [
    N.NAME,
    L.NAME,
    V.NAME,
    C.NAME,
    D.NAME,
    R.NAME,
    m.NAME,
    w.NAME,
    M.NAME,
  ];
}
class v extends f {
  constructor(e) {
    super(e), (this.name = "LazyDecodingError");
  }
}
class fe {
  sections = new Map();
  encodedString;
  decoded;
  dirty;
  constructor(e) {
    e
      ? ((this.encodedString = e), (this.decoded = !1), (this.dirty = !1))
      : ((this.encodedString = "DBAA"), (this.decoded = !1), (this.dirty = !1));
  }
  setFieldValue(e, t, n) {
    if (
      !this.decoded &&
      this.encodedString != null &&
      this.encodedString.length > 0
    )
      try {
        this.decode(this.encodedString);
      } catch (r) {
        throw new v(r.message);
      }
    let i = null;
    if (
      (this.sections.has(e)
        ? (i = this.sections.get(e))
        : e === L.NAME
        ? ((i = new L()), this.sections.set(L.NAME, i))
        : e === N.NAME
        ? ((i = new N()), this.sections.set(N.NAME, i))
        : e === V.NAME
        ? ((i = new V()), this.sections.set(V.NAME, i))
        : e === C.NAME
        ? ((i = new C()), this.sections.set(C.NAME, i))
        : e === D.NAME
        ? ((i = new D()), this.sections.set(D.NAME, i))
        : e === R.NAME
        ? ((i = new R()), this.sections.set(R.NAME, i))
        : e === m.NAME
        ? ((i = new m()), this.sections.set(m.NAME, i))
        : e === w.NAME
        ? ((i = new w()), this.sections.set(w.NAME, i))
        : e === M.NAME && ((i = new M()), this.sections.set(M.NAME, i)),
      i)
    )
      i.setFieldValue(t, n), (this.dirty = !0);
    else throw new Ne(e + "." + t + " not found");
  }
  setFieldValueBySectionId(e, t, n) {
    this.setFieldValue(A.SECTION_ID_NAME_MAP.get(e), t, n);
  }
  getFieldValue(e, t) {
    if (
      !this.decoded &&
      this.encodedString != null &&
      this.encodedString.length > 0
    )
      try {
        this.decode(this.encodedString);
      } catch (n) {
        throw new v(n.message);
      }
    return this.sections.has(e) ? this.sections.get(e).getFieldValue(t) : null;
  }
  getFieldValueBySectionId(e, t) {
    return this.getFieldValue(A.SECTION_ID_NAME_MAP.get(e), t);
  }
  hasField(e, t) {
    if (
      !this.decoded &&
      this.encodedString != null &&
      this.encodedString.length > 0
    )
      try {
        this.decode(this.encodedString);
      } catch (n) {
        throw new v(n.message);
      }
    return this.sections.has(e) ? this.sections.get(e).hasField(t) : !1;
  }
  hasFieldBySectionId(e, t) {
    return this.hasField(A.SECTION_ID_NAME_MAP.get(e), t);
  }
  hasSection(e) {
    if (
      !this.decoded &&
      this.encodedString != null &&
      this.encodedString.length > 0
    )
      try {
        this.decode(this.encodedString);
      } catch (t) {
        throw new v(t.message);
      }
    return this.sections.has(e);
  }
  hasSectionId(e) {
    return this.hasSection(A.SECTION_ID_NAME_MAP.get(e));
  }
  deleteSection(e) {
    if (
      !this.decoded &&
      this.encodedString != null &&
      this.encodedString.length > 0
    )
      try {
        this.decode(this.encodedString);
      } catch (t) {
        throw new v(t.message);
      }
    this.sections.delete(e), (this.dirty = !0);
  }
  deleteSectionById(e) {
    this.deleteSection(A.SECTION_ID_NAME_MAP.get(e));
  }
  clear() {
    this.sections.clear(),
      (this.encodedString = "DBAA"),
      (this.decoded = !1),
      (this.dirty = !1);
  }
  getHeader() {
    if (
      !this.decoded &&
      this.encodedString != null &&
      this.encodedString.length > 0
    )
      try {
        this.decode(this.encodedString);
      } catch (t) {
        throw new v(t.message);
      }
    let e = new F();
    return e.setFieldValue("SectionIds", this.getSectionIds()), e.toObj();
  }
  getSection(e) {
    if (
      !this.decoded &&
      this.encodedString != null &&
      this.encodedString.length > 0
    )
      try {
        this.decode(this.encodedString);
      } catch (t) {
        throw new v(t.message);
      }
    return this.sections.has(e) ? this.sections.get(e).toObj() : null;
  }
  getSectionIds() {
    if (
      !this.decoded &&
      this.encodedString != null &&
      this.encodedString.length > 0
    )
      try {
        this.decode(this.encodedString);
      } catch (t) {
        throw new v(t.message);
      }
    let e = [];
    for (let t = 0; t < A.SECTION_ORDER.length; t++) {
      let n = A.SECTION_ORDER[t];
      if (this.sections.has(n)) {
        let i = this.sections.get(n);
        e.push(i.getId());
      }
    }
    return e;
  }
  encode() {
    if (!this.dirty) return this.encodedString;
    if (
      !this.decoded &&
      this.encodedString != null &&
      this.encodedString.length > 0
    )
      try {
        this.decode(this.encodedString);
      } catch (i) {
        throw new v(i.message);
      }
    let e = [],
      t = [];
    for (let i = 0; i < A.SECTION_ORDER.length; i++) {
      let r = A.SECTION_ORDER[i];
      if (this.sections.has(r)) {
        let o = this.sections.get(r);
        e.push(o.encode()), t.push(o.getId());
      }
    }
    let n = new F();
    return (
      n.setFieldValue("SectionIds", this.getSectionIds()),
      e.unshift(n.encode()),
      (this.encodedString = e.join("~")),
      (this.dirty = !1),
      this.encodedString
    );
  }
  decode(e) {
    (this.encodedString = e),
      (this.decoded = !1),
      (this.dirty = !0),
      this.sections.clear();
    let t = e.split("~"),
      n = new F(t[0]);
    this.sections.set(F.NAME, n);
    let i = n.getFieldValue("SectionIds");
    for (let r = 0; r < i.length; r++)
      if (i[r] === L.ID) {
        let o = new L(t[r + 1]);
        this.sections.set(L.NAME, o);
      } else if (i[r] === N.ID) {
        let o = new N(t[r + 1]);
        this.sections.set(N.NAME, o);
      } else if (i[r] === V.ID) {
        let o = new V(t[r + 1]);
        this.sections.set(V.NAME, o);
      } else if (i[r] === C.ID) {
        let o = new C(t[r + 1]);
        this.sections.set(C.NAME, o);
      } else if (i[r] === D.ID) {
        let o = new D(t[r + 1]);
        this.sections.set(D.NAME, o);
      } else if (i[r] === R.ID) {
        let o = new R(t[r + 1]);
        this.sections.set(R.NAME, o);
      } else if (i[r] === m.ID) {
        let o = new m(t[r + 1]);
        this.sections.set(m.NAME, o);
      } else if (i[r] === w.ID) {
        let o = new w(t[r + 1]);
        this.sections.set(w.NAME, o);
      } else if (i[r] === M.ID) {
        let o = new M(t[r + 1]);
        this.sections.set(M.NAME, o);
      }
    (this.decoded = !0), (this.dirty = !1);
  }
  encodeSection(e) {
    if (
      !this.decoded &&
      this.encodedString != null &&
      this.encodedString.length > 0
    )
      try {
        this.decode(this.encodedString);
      } catch (t) {
        throw new v(t.message);
      }
    return this.sections.has(e) ? this.sections.get(e).encode() : null;
  }
  encodeSectionById(e) {
    return this.encodeSection(A.SECTION_ID_NAME_MAP.get(e));
  }
  decodeSection(e, t) {
    if (
      !this.decoded &&
      this.encodedString != null &&
      this.encodedString.length > 0
    )
      try {
        this.decode(this.encodedString);
      } catch (i) {
        throw new v(i.message);
      }
    let n = null;
    this.sections.has(e)
      ? (n = this.sections.get(e))
      : e === L.NAME
      ? ((n = new L()), this.sections.set(L.NAME, n))
      : e === N.NAME
      ? ((n = new N()), this.sections.set(N.NAME, n))
      : e === V.NAME
      ? ((n = new V()), this.sections.set(V.NAME, n))
      : e === C.NAME
      ? ((n = new C()), this.sections.set(C.NAME, n))
      : e === D.NAME
      ? ((n = new D()), this.sections.set(D.NAME, n))
      : e === R.NAME
      ? ((n = new R()), this.sections.set(R.NAME, n))
      : e === m.NAME
      ? ((n = new m()), this.sections.set(m.NAME, n))
      : e === w.NAME
      ? ((n = new w()), this.sections.set(w.NAME, n))
      : e === M.NAME && ((n = new M()), this.sections.set(M.NAME, n)),
      n && n.decode(t);
  }
  decodeSectionById(e, t) {
    this.decodeSection(A.SECTION_ID_NAME_MAP.get(e), t);
  }
  toObject() {
    if (
      !this.decoded &&
      this.encodedString != null &&
      this.encodedString.length > 0
    )
      try {
        this.decode(this.encodedString);
      } catch (t) {
        throw new v(t.message);
      }
    let e = {};
    for (let t = 0; t < A.SECTION_ORDER.length; t++) {
      let n = A.SECTION_ORDER[t];
      this.sections.has(n) && (e[n] = this.sections.get(n).toObj());
    }
    return e;
  }
}
class Ke {
  gppVersion = "1.1";
  supportedAPIs = [];
  eventQueue = new Fe(this);
  cmpStatus = Q.LOADING;
  cmpDisplayStatus = k.HIDDEN;
  signalStatus = B.NOT_READY;
  applicableSections = [];
  gppModel = new fe();
  cmpId;
  cmpVersion;
  eventStatus;
  reset() {
    this.eventQueue.clear(),
      (this.cmpStatus = Q.LOADING),
      (this.cmpDisplayStatus = k.HIDDEN),
      (this.signalStatus = B.NOT_READY),
      (this.applicableSections = []),
      (this.supportedAPIs = []),
      (this.gppModel = new fe()),
      delete this.cmpId,
      delete this.cmpVersion,
      delete this.eventStatus;
  }
}
class _e {
  static absCall(e, t, n, i) {
    return new Promise((r, o) => {
      const S = new XMLHttpRequest(),
        T = () => {
          if (S.readyState == XMLHttpRequest.DONE)
            if (S.status >= 200 && S.status < 300) {
              let Y = S.response;
              if (typeof Y == "string")
                try {
                  Y = JSON.parse(Y);
                } catch {}
              r(Y);
            } else
              o(
                new Error(
                  `HTTP Status: ${S.status} response type: ${S.responseType}`
                )
              );
        },
        h = () => {
          o(new Error("error"));
        },
        P = () => {
          o(new Error("aborted"));
        },
        I = () => {
          o(new Error("Timeout " + i + "ms " + e));
        };
      (S.withCredentials = n),
        S.addEventListener("load", T),
        S.addEventListener("error", h),
        S.addEventListener("abort", P),
        t === null ? S.open("GET", e, !0) : S.open("POST", e, !0),
        (S.responseType = "json"),
        (S.timeout = i),
        (S.ontimeout = I),
        S.send(t);
    });
  }
  static post(e, t, n = !1, i = 0) {
    return this.absCall(e, JSON.stringify(t), n, i);
  }
  static fetch(e, t = !1, n = 0) {
    return this.absCall(e, null, t, n);
  }
}
class le extends Error {
  constructor(e) {
    super(e), (this.name = "GVLError");
  }
}
class ee {
  static langSet = new Set([
    "BG",
    "CA",
    "CS",
    "DA",
    "DE",
    "EL",
    "EN",
    "ES",
    "ET",
    "FI",
    "FR",
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
    "PT",
    "RO",
    "RU",
    "SK",
    "SL",
    "SV",
    "TR",
    "ZH",
  ]);
  has(e) {
    return ee.langSet.has(e);
  }
  forEach(e) {
    ee.langSet.forEach(e);
  }
  get size() {
    return ee.langSet.size;
  }
}
class Z {
  vendors;
  static DEFAULT_LANGUAGE = "EN";
  consentLanguages = new ee();
  gvlSpecificationVersion;
  vendorListVersion;
  tcfPolicyVersion;
  lastUpdated;
  purposes;
  specialPurposes;
  features;
  specialFeatures;
  stacks;
  dataCategories;
  language = Z.DEFAULT_LANGUAGE;
  vendorIds;
  ready = !1;
  fullVendorList;
  byPurposeVendorMap;
  bySpecialPurposeVendorMap;
  byFeatureVendorMap;
  bySpecialFeatureVendorMap;
  baseUrl;
  languageFilename = "purposes-[LANG].json";
  static fromVendorList(e) {
    let t = new Z();
    return t.populate(e), t;
  }
  static async fromUrl(e) {
    let t = e.baseUrl;
    if (!t || t.length === 0) throw new le("Invalid baseUrl: '" + t + "'");
    if (/^https?:\/\/vendorlist\.consensu\.org\//.test(t))
      throw new le(
        "Invalid baseUrl!  You may not pull directly from vendorlist.consensu.org and must provide your own cache"
      );
    t.length > 0 && t[t.length - 1] !== "/" && (t += "/");
    let n = new Z();
    if (
      ((n.baseUrl = t),
      e.languageFilename
        ? (n.languageFilename = e.languageFilename)
        : (n.languageFilename = "purposes-[LANG].json"),
      e.version > 0)
    ) {
      let i = e.versionedFilename;
      i || (i = "archives/vendor-list-v[VERSION].json");
      let r = t + i.replace("[VERSION]", String(e.version));
      n.populate(await _e.fetch(r));
    } else {
      let i = e.latestFilename;
      i || (i = "vendor-list.json");
      let r = t + i;
      n.populate(await _e.fetch(r));
    }
    return n;
  }
  async changeLanguage(e) {
    const t = e.toUpperCase();
    if (this.consentLanguages.has(t)) {
      if (t !== this.language) {
        this.language = t;
        const n = this.baseUrl + this.languageFilename.replace("[LANG]", e);
        try {
          this.populate(await _e.fetch(n));
        } catch (i) {
          throw new le("unable to load language: " + i.message);
        }
      }
    } else throw new le(`unsupported language ${e}`);
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
        (this.vendors = e.vendors),
        (this.fullVendorList = e.vendors),
        this.mapVendors(),
        (this.ready = !0));
  }
  mapVendors(e) {
    (this.byPurposeVendorMap = {}),
      (this.bySpecialPurposeVendorMap = {}),
      (this.byFeatureVendorMap = {}),
      (this.bySpecialFeatureVendorMap = {}),
      Object.keys(this.purposes).forEach((t) => {
        this.byPurposeVendorMap[t] = {
          legInt: new Set(),
          consent: new Set(),
          flexible: new Set(),
        };
      }),
      Object.keys(this.specialPurposes).forEach((t) => {
        this.bySpecialPurposeVendorMap[t] = new Set();
      }),
      Object.keys(this.features).forEach((t) => {
        this.byFeatureVendorMap[t] = new Set();
      }),
      Object.keys(this.specialFeatures).forEach((t) => {
        this.bySpecialFeatureVendorMap[t] = new Set();
      }),
      Array.isArray(e) || (e = Object.keys(this.fullVendorList).map((t) => +t)),
      (this.vendorIds = new Set(e)),
      (this.vendors = e.reduce((t, n) => {
        const i = this.vendors[String(n)];
        return (
          i &&
            i.deletedDate === void 0 &&
            (i.purposes.forEach((r) => {
              this.byPurposeVendorMap[String(r)].consent.add(n);
            }),
            i.specialPurposes.forEach((r) => {
              this.bySpecialPurposeVendorMap[String(r)].add(n);
            }),
            i.legIntPurposes.forEach((r) => {
              this.byPurposeVendorMap[String(r)].legInt.add(n);
            }),
            i.flexiblePurposes &&
              i.flexiblePurposes.forEach((r) => {
                this.byPurposeVendorMap[String(r)].flexible.add(n);
              }),
            i.features.forEach((r) => {
              this.byFeatureVendorMap[String(r)].add(n);
            }),
            i.specialFeatures.forEach((r) => {
              this.bySpecialFeatureVendorMap[String(r)].add(n);
            }),
            (t[n] = i)),
          t
        );
      }, {}));
  }
  getFilteredVendors(e, t, n, i) {
    const r = e.charAt(0).toUpperCase() + e.slice(1);
    let o;
    const S = {};
    return (
      e === "purpose" && n
        ? (o = this["by" + r + "VendorMap"][String(t)][n])
        : (o = this["by" + (i ? "Special" : "") + r + "VendorMap"][String(t)]),
      o.forEach((T) => {
        S[String(T)] = this.vendors[String(T)];
      }),
      S
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
  narrowVendorsTo(e) {
    this.mapVendors(e);
  }
  get isReady() {
    return this.ready;
  }
  static isInstanceOf(e) {
    return typeof e == "object" && typeof e.narrowVendorsTo == "function";
  }
}
class We {
  callResponder;
  cmpApiContext;
  constructor(e, t, n) {
    (this.cmpApiContext = new Ke()),
      (this.cmpApiContext.cmpId = e),
      (this.cmpApiContext.cmpVersion = t),
      (this.callResponder = new He(this.cmpApiContext, n));
  }
  fireEvent(e, t) {
    this.cmpApiContext.eventQueue.exec(e, t);
  }
  fireErrorEvent(e) {
    this.cmpApiContext.eventQueue.exec("error", e);
  }
  fireSectionChange(e) {
    this.cmpApiContext.eventQueue.exec("sectionChange", e);
  }
  getEventStatus() {
    return this.cmpApiContext.eventStatus;
  }
  setEventStatus(e) {
    this.cmpApiContext.eventStatus = e;
  }
  getCmpStatus() {
    return this.cmpApiContext.cmpStatus;
  }
  setCmpStatus(e) {
    (this.cmpApiContext.cmpStatus = e),
      this.cmpApiContext.eventQueue.exec("cmpStatus", e);
  }
  getCmpDisplayStatus() {
    return this.cmpApiContext.cmpDisplayStatus;
  }
  setCmpDisplayStatus(e) {
    (this.cmpApiContext.cmpDisplayStatus = e),
      this.cmpApiContext.eventQueue.exec("cmpDisplayStatus", e);
  }
  getSignalStatus() {
    return this.cmpApiContext.signalStatus;
  }
  setSignalStatus(e) {
    (this.cmpApiContext.signalStatus = e),
      this.cmpApiContext.eventQueue.exec("signalStatus", e);
  }
  getApplicableSections() {
    return this.cmpApiContext.applicableSections;
  }
  setApplicableSections(e) {
    this.cmpApiContext.applicableSections = e;
  }
  getSupportedAPIs() {
    return this.cmpApiContext.supportedAPIs;
  }
  setSupportedAPIs(e) {
    this.cmpApiContext.supportedAPIs = e;
  }
  setGppString(e) {
    this.cmpApiContext.gppModel.decode(e);
  }
  getGppString() {
    return this.cmpApiContext.gppModel.encode();
  }
  setSectionString(e, t) {
    this.cmpApiContext.gppModel.decodeSection(e, t);
  }
  setSectionStringById(e, t) {
    this.setSectionString(A.SECTION_ID_NAME_MAP.get(e), t);
  }
  getSectionString(e) {
    return this.cmpApiContext.gppModel.encodeSection(e);
  }
  getSectionStringById(e) {
    return this.getSectionString(A.SECTION_ID_NAME_MAP.get(e));
  }
  setFieldValue(e, t, n) {
    this.cmpApiContext.gppModel.setFieldValue(e, t, n);
  }
  setFieldValueBySectionId(e, t, n) {
    this.setFieldValue(A.SECTION_ID_NAME_MAP.get(e), t, n);
  }
  getFieldValue(e, t) {
    return this.cmpApiContext.gppModel.getFieldValue(e, t);
  }
  getFieldValueBySectionId(e, t) {
    return this.getFieldValue(A.SECTION_ID_NAME_MAP.get(e), t);
  }
  getSection(e) {
    return this.cmpApiContext.gppModel.getSection(e);
  }
  getSectionById(e) {
    return this.getSection(A.SECTION_ID_NAME_MAP.get(e));
  }
  hasSection(e) {
    return this.cmpApiContext.gppModel.hasSection(e);
  }
  hasSectionId(e) {
    return this.hasSection(A.SECTION_ID_NAME_MAP.get(e));
  }
  deleteSection(e) {
    this.cmpApiContext.gppModel.deleteSection(e);
  }
  deleteSectionById(e) {
    this.deleteSection(A.SECTION_ID_NAME_MAP.get(e));
  }
  clear() {
    this.cmpApiContext.gppModel.clear();
  }
  getObject() {
    return this.cmpApiContext.gppModel.toObject();
  }
  getGvlFromVendorList(e) {
    return Z.fromVendorList(e);
  }
  async getGvlFromUrl(e) {
    return Z.fromUrl(e);
  }
}
const Pe = "__gppLocator",
  Ce = (s) => {
    if (!window.frames[s])
      if (window.document.body) {
        const e = window.document.createElement("iframe");
        (e.style.cssText = "display:none"),
          (e.name = s),
          window.document.body.appendChild(e);
      } else setTimeout(Ce, 5);
  },
  je = (s) => {
    let e = window,
      t;
    for (; e; ) {
      try {
        if (e.frames[s]) {
          t = e;
          break;
        }
      } catch {}
      if (e === window.top) break;
      e = e.parent;
    }
    return t;
  },
  Qe = (s) => typeof s == "object" && s != null && "__gppCall" in s,
  Xe = () => {
    const s = [],
      e = [];
    let t;
    const n = (r, o, S, T) => {
        if (r === "queue") return s;
        if (r === "events") return e;
        const h = {
          gppVersion: "1.1",
          cmpStatus: Q.STUB,
          cmpDisplayStatus: k.HIDDEN,
          signalStatus: B.NOT_READY,
          supportedAPIs: [],
          cmpId: 0,
          sectionList: [],
          applicableSections: [0],
          gppString: "",
          parsedSections: {},
        };
        if (r === "ping") o(h, !0);
        else if (r === "addEventListener") {
          t || (t = 0), (t += 1);
          const P = t;
          e.push({ id: P, callback: o, parameter: S }),
            o(
              {
                eventName: "listenerRegistered",
                listenerId: P,
                data: !0,
                pingData: h,
              },
              !0
            );
        } else if (r === "removeEventListener") {
          let P = !1;
          for (let I = 0; I < e.length; I++)
            if (e[I].id === S) {
              e.splice(I, 1), (P = !0);
              break;
            }
          o(
            {
              eventName: "listenerRemoved",
              listenerId: S,
              data: P,
              pingData: h,
            },
            !0
          );
        } else
          r === "hasSection"
            ? o(!1, !0)
            : r === "getSection" || r === "getField"
            ? o(null, !0)
            : s.push([].slice.apply([r, o, S, T]));
        return null;
      },
      i = (r) => {
        const o = typeof r.data == "string";
        let S = {};
        if (o)
          try {
            S = JSON.parse(r.data);
          } catch {
            S = {};
          }
        else S = r.data;
        if (!Qe(S)) return null;
        if (S.__gppCall && window.__gpp) {
          const T = S.__gppCall;
          window.__gpp(
            T.command,
            (h, P) => {
              const I = {
                __gppReturn: { returnValue: h, success: P, callId: T.callId },
              };
              r &&
                r.source &&
                r.source.postMessage &&
                r.source.postMessage(o ? JSON.stringify(I) : I, "*");
            },
            "parameter" in T ? T.parameter : void 0,
            "version" in T ? T.version : "1.1"
          );
        }
        return null;
      };
    je(Pe) ||
      (Ce(Pe), (window.__gpp = n), window.addEventListener("message", i, !1));
  };
var $e = ((s) => (
    (s.CONSENT = "Consent"),
    (s.CONTRACT = "Contract"),
    (s.LEGAL_OBLIGATIONS = "Legal obligations"),
    (s.VITAL_INTERESTS = "Vital interests"),
    (s.PUBLIC_INTEREST = "Public interest"),
    (s.LEGITIMATE_INTERESTS = "Legitimate interests"),
    s
  ))($e || {}),
  ce = ((s) => (
    (s.CONSENT = "Consent"),
    (s.LEGITIMATE_INTERESTS = "Legitimate interests"),
    s
  ))(ce || {});
const De = 407,
  qe = ",",
  ze = [
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
  ];
ze
  .filter(
    ({ experienceKey: s }) =>
      s !== "tcf_features" && s !== "tcf_special_purposes"
  )
  .map((s) => s.experienceKey),
  ce.CONSENT,
  ce.LEGITIMATE_INTERESTS;
const Je = (s) => {
  if (!window.Fides.options.fidesTcfGdprApplies) return null;
  const { fides_string: e } = s.detail;
  if (e) {
    const [t] = e.split(qe);
    return t.split(".")[0];
  }
  return e ?? "";
};
var Re;
((s) => {
  ((e) => ((e[(e._0 = 0)] = "_0"), (e[(e._1 = 1)] = "_1")))(
    s.IABTCFgdprApplies || (s.IABTCFgdprApplies = {})
  ),
    ((e) => ((e[(e._0 = 0)] = "_0"), (e[(e._1 = 1)] = "_1")))(
      s.IABTCFPurposeOneTreatment || (s.IABTCFPurposeOneTreatment = {})
    ),
    ((e) => ((e[(e._0 = 0)] = "_0"), (e[(e._1 = 1)] = "_1")))(
      s.IABTCFUseNonStandardTexts || (s.IABTCFUseNonStandardTexts = {})
    );
})(Re || (Re = {}));
var Ze = ((s) => (
    (s.FRONTEND = "frontend"),
    (s.SYSTEM_WIDE = "system_wide"),
    (s.NOT_APPLICABLE = "not_applicable"),
    s
  ))(Ze || {}),
  et = ((s) => (
    (s.OPT_IN = "opt_in"),
    (s.OPT_OUT = "opt_out"),
    (s.NOTICE_ONLY = "notice_only"),
    s
  ))(et || {}),
  tt = ((s) => (
    (s.OPT_IN = "opt_in"),
    (s.OPT_OUT = "opt_out"),
    (s.ACKNOWLEDGE = "acknowledge"),
    s
  ))(tt || {}),
  me = ((s) => (
    (s.OVERLAY = "overlay"),
    (s.PRIVACY_CENTER = "privacy_center"),
    (s.TCF_OVERLAY = "tcf_overlay"),
    s
  ))(me || {}),
  st = ((s) => (
    (s.ALWAYS_ENABLED = "always_enabled"),
    (s.ENABLED_WHERE_REQUIRED = "enabled_where_required"),
    (s.ALWAYS_DISABLED = "always_disabled"),
    s
  ))(st || {}),
  nt = ((s) => (
    (s.PRIMARY = "primary"),
    (s.SECONDARY = "secondary"),
    (s.TERTIARY = "tertiary"),
    s
  ))(nt || {}),
  it = ((s) => (
    (s.BUTTON = "button"),
    (s.REJECT = "reject"),
    (s.ACCEPT = "accept"),
    (s.SAVE = "save"),
    (s.DISMISS = "dismiss"),
    (s.GPC = "gpc"),
    (s.INDIVIDUAL_NOTICE = "individual_notice"),
    s
  ))(it || {}),
  rt = ((s) => (
    (s.privacy_center = "privacy_center"),
    (s.overlay = "overlay"),
    (s.api = "api"),
    s
  ))(rt || {}),
  ot = ((s) => (
    (s.NONE = "none"), (s.APPLIED = "applied"), (s.OVERRIDDEN = "overridden"), s
  ))(ot || {}),
  lt = ((s) => (
    (s.OVERLAY = "overlay"),
    (s.BANNER = "banner"),
    (s.PRIVACY_CENTER = "privacy_center"),
    (s.TCF_OVERLAY = "tcf_overlay"),
    (s.TCF_BANNER = "tcf_banner"),
    s
  ))(lt || {});
const at = (s, e) => !!Object.hasOwn(e.consent, s.notice_key),
  de = (s) =>
    !s || typeof s != "object" ? !1 : Object.keys(s).length === 0 || "id" in s,
  St = (s, e) => {
    var t, n;
    return s.component === me.TCF_OVERLAY
      ? (t = s.meta) != null && t.version_hash
        ? s.meta.version_hash !== e.tcf_version_hash
        : !0
      : s?.privacy_notices == null || s.privacy_notices.length === 0
      ? !1
      : !((n = s.privacy_notices) != null && n.every((i) => at(i, e)));
  },
  we = {
    data_sales_and_sharing: {
      us: {
        gpp_notice_fields: [
          E.SALE_OPT_OUT_NOTICE,
          E.SHARING_OPT_OUT_NOTICE,
          E.SHARING_NOTICE,
        ],
        gpp_mechanism_fields: [
          {
            field: E.SALE_OPT_OUT,
            not_available: 0,
            opt_out: 1,
            not_opt_out: 2,
          },
          {
            field: E.SHARING_OPT_OUT,
            not_available: 0,
            opt_out: 1,
            not_opt_out: 2,
          },
        ],
      },
      us_ca: {
        gpp_notice_fields: [c.SALE_OPT_OUT_NOTICE, c.SHARING_OPT_OUT_NOTICE],
        gpp_mechanism_fields: [
          {
            field: c.SALE_OPT_OUT,
            not_available: 0,
            opt_out: 1,
            not_opt_out: 2,
          },
          {
            field: c.SHARING_OPT_OUT,
            not_available: 0,
            opt_out: 1,
            not_opt_out: 2,
          },
        ],
      },
    },
    targeted_advertising: {
      us: {
        gpp_notice_fields: [E.TARGETED_ADVERTISING_OPT_OUT_NOTICE],
        gpp_mechanism_fields: [
          {
            field: E.TARGETED_ADVERTISING_OPT_OUT,
            not_available: 0,
            opt_out: 1,
            not_opt_out: 2,
          },
        ],
      },
      us_co: {
        gpp_notice_fields: [d.TARGETED_ADVERTISING_OPT_OUT_NOTICE],
        gpp_mechanism_fields: [
          {
            field: d.TARGETED_ADVERTISING_OPT_OUT,
            not_available: 0,
            opt_out: 1,
            not_opt_out: 2,
          },
        ],
      },
      us_ct: {
        gpp_notice_fields: [g.TARGETED_ADVERTISING_OPT_OUT_NOTICE],
        gpp_mechanism_fields: [
          {
            field: g.TARGETED_ADVERTISING_OPT_OUT,
            not_available: 0,
            opt_out: 1,
            not_opt_out: 2,
          },
        ],
      },
      us_ut: {
        gpp_notice_fields: [u.TARGETED_ADVERTISING_OPT_OUT_NOTICE],
        gpp_mechanism_fields: [
          {
            field: u.TARGETED_ADVERTISING_OPT_OUT,
            not_available: 0,
            opt_out: 1,
            not_opt_out: 2,
          },
        ],
      },
      us_va: {
        gpp_notice_fields: [p.TARGETED_ADVERTISING_OPT_OUT_NOTICE],
        gpp_mechanism_fields: [
          {
            field: p.TARGETED_ADVERTISING_OPT_OUT,
            not_available: 0,
            opt_out: 1,
            not_opt_out: 2,
          },
        ],
      },
      us_ia: { gpp_notice_fields: [], gpp_mechanism_fields: [] },
    },
    data_sharing: {
      us_ut: {
        gpp_notice_fields: [u.SHARING_NOTICE],
        gpp_mechanism_fields: [],
      },
      us_va: {
        gpp_notice_fields: [p.SHARING_NOTICE],
        gpp_mechanism_fields: [],
      },
      us_co: {
        gpp_notice_fields: [d.SHARING_NOTICE],
        gpp_mechanism_fields: [],
      },
      us_ct: {
        gpp_notice_fields: [g.SHARING_NOTICE],
        gpp_mechanism_fields: [],
      },
    },
    data_sales: {
      us_co: {
        gpp_notice_fields: [d.SALE_OPT_OUT_NOTICE],
        gpp_mechanism_fields: [
          {
            field: d.SALE_OPT_OUT,
            not_available: 0,
            opt_out: 1,
            not_opt_out: 2,
          },
        ],
      },
      us_ct: {
        gpp_notice_fields: [g.SALE_OPT_OUT_NOTICE],
        gpp_mechanism_fields: [
          {
            field: g.SALE_OPT_OUT,
            not_available: 0,
            opt_out: 1,
            not_opt_out: 2,
          },
        ],
      },
      us_ut: {
        gpp_notice_fields: [u.SALE_OPT_OUT_NOTICE],
        gpp_mechanism_fields: [
          {
            field: u.SALE_OPT_OUT,
            not_available: 0,
            opt_out: 1,
            not_opt_out: 2,
          },
        ],
      },
      us_va: {
        gpp_notice_fields: [p.SALE_OPT_OUT_NOTICE],
        gpp_mechanism_fields: [
          {
            field: p.SALE_OPT_OUT,
            not_available: 0,
            opt_out: 1,
            not_opt_out: 2,
          },
        ],
      },
      us_ia: { gpp_notice_fields: [], gpp_mechanism_fields: [] },
    },
    sensitive_personal_data_sharing: {
      us: {
        gpp_notice_fields: [
          E.SENSITIVE_DATA_LIMIT_USE_NOTICE,
          E.SENSITIVE_DATA_PROCESSING_OPT_OUT_NOTICE,
        ],
        gpp_mechanism_fields: [
          {
            field: E.SENSITIVE_DATA_PROCESSING,
            not_available: Array(12).fill(0),
            opt_out: Array(12).fill(1),
            not_opt_out: Array(12).fill(2),
          },
        ],
      },
      us_ca: {
        gpp_notice_fields: [c.SENSITIVE_DATA_LIMIT_USE_NOTICE],
        gpp_mechanism_fields: [
          {
            field: c.SENSITIVE_DATA_PROCESSING,
            not_available: Array(9).fill(0),
            opt_out: Array(9).fill(1),
            not_opt_out: Array(9).fill(2),
          },
        ],
      },
      us_ut: {
        gpp_notice_fields: [u.SENSITIVE_DATA_PROCESSING_OPT_OUT_NOTICE],
        gpp_mechanism_fields: [
          {
            field: u.SENSITIVE_DATA_PROCESSING,
            not_available: Array(8).fill(0),
            opt_out: Array(8).fill(1),
            not_opt_out: Array(8).fill(2),
          },
        ],
      },
      us_va: {
        gpp_notice_fields: [],
        gpp_mechanism_fields: [
          {
            field: p.SENSITIVE_DATA_PROCESSING,
            not_available: Array(8).fill(0),
            opt_out: Array(8).fill(1),
            not_opt_out: Array(8).fill(2),
          },
        ],
      },
      us_co: {
        gpp_notice_fields: [],
        gpp_mechanism_fields: [
          {
            field: d.SENSITIVE_DATA_PROCESSING,
            not_available: Array(7).fill(0),
            opt_out: Array(7).fill(1),
            not_opt_out: Array(7).fill(2),
          },
        ],
      },
      us_ct: {
        gpp_notice_fields: [],
        gpp_mechanism_fields: [
          {
            field: g.SENSITIVE_DATA_PROCESSING,
            not_available: Array(8).fill(0),
            opt_out: Array(8).fill(1),
            not_opt_out: Array(8).fill(2),
          },
        ],
      },
    },
    known_child_sensitive_data_consents: {
      us: {
        gpp_notice_fields: [],
        gpp_mechanism_fields: [
          {
            field: E.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS,
            not_available: Array(2).fill(0),
            opt_out: Array(2).fill(1),
            not_opt_out: Array(2).fill(2),
          },
        ],
      },
      us_ca: {
        gpp_notice_fields: [],
        gpp_mechanism_fields: [
          {
            field: c.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS,
            not_available: Array(2).fill(0),
            opt_out: Array(2).fill(1),
            not_opt_out: Array(2).fill(2),
          },
        ],
      },
      us_ut: {
        gpp_notice_fields: [],
        gpp_mechanism_fields: [
          {
            field: u.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS,
            not_available: 0,
            opt_out: 1,
            not_opt_out: 2,
          },
        ],
      },
      us_va: {
        gpp_notice_fields: [],
        gpp_mechanism_fields: [
          {
            field: p.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS,
            not_available: 0,
            opt_out: 1,
            not_opt_out: 2,
          },
        ],
      },
      us_co: {
        gpp_notice_fields: [],
        gpp_mechanism_fields: [
          {
            field: d.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS,
            not_available: 0,
            opt_out: 1,
            not_opt_out: 2,
          },
        ],
      },
      us_ct: {
        gpp_notice_fields: [],
        gpp_mechanism_fields: [
          {
            field: g.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS,
            not_available: Array(3).fill(0),
            opt_out: Array(3).fill(1),
            not_opt_out: Array(3).fill(2),
          },
        ],
      },
    },
    personal_data_consents: {
      us: {
        gpp_notice_fields: [],
        gpp_mechanism_fields: [
          {
            field: E.PERSONAL_DATA_CONSENTS,
            not_available: 0,
            opt_out: 1,
            not_opt_out: 2,
          },
        ],
      },
      us_ca: {
        gpp_notice_fields: [],
        gpp_mechanism_fields: [
          {
            field: c.PERSONAL_DATA_CONSENTS,
            not_available: 0,
            opt_out: 1,
            not_opt_out: 2,
          },
        ],
      },
    },
  },
  ge = {
    us: { name: C.NAME, id: C.ID, prefix: "usnat" },
    us_ca: { name: D.NAME, id: D.ID, prefix: "usca" },
    us_ct: { name: M.NAME, id: M.ID, prefix: "usct" },
    us_co: { name: m.NAME, id: m.ID, prefix: "usco" },
    us_ut: { name: w.NAME, id: w.ID, prefix: "usut" },
    us_va: { name: R.NAME, id: R.ID, prefix: "usva" },
  },
  Me = ({ cmpApi: s, experience: e }) => {
    const t = new Set(),
      { privacy_notices: n, region: i } = e;
    return (
      Object.entries(we).forEach(([r, o]) => {
        const S = o[i];
        if (S) {
          const { gpp_notice_fields: T } = S,
            h = n != null && n.find((I) => I.notice_key === r) ? 1 : 2,
            P = ge[i];
          t.add(P),
            T.forEach((I) => {
              s.setFieldValue(P.name, I, h);
            });
        }
      }),
      Array.from(t)
    );
  },
  Le = ({ cmpApi: s, cookie: e, region: t }) => {
    const n = new Set(),
      { consent: i } = e;
    return (
      Object.entries(we).forEach(([r, o]) => {
        const S = o[t];
        if (S) {
          const { gpp_mechanism_fields: T } = S,
            h = i[r],
            P = ge[t];
          n.add(P),
            T.forEach((I) => {
              let Y = I.not_available;
              h === !1 ? (Y = I.opt_out) : h && (Y = I.not_opt_out),
                s.setFieldValue(P.name, I.field, Y);
            });
        }
      }),
      Array.from(n)
    );
  },
  Et = 1,
  Ve = (s, e) => {
    if (!window.Fides.options.tcfEnabled) return !1;
    const t = Je(s);
    return t
      ? (e.setFieldValueBySectionId(N.ID, "CmpId", De),
        e.setSectionStringById(N.ID, t),
        !0)
      : !1;
  },
  _t = () => {
    const s = [];
    if (window.Fides.options.tcfEnabled) return s.push(`${N.ID}:${N.NAME}`), s;
    if (de(window.Fides.experience)) {
      const { gpp_settings: e } = window.Fides.experience;
      if (e && e.enabled && e.regions) {
        const t = Object.values(ge);
        e.regions.forEach((n) => {
          const i = t.find((r) => r.prefix === n);
          i && s.push(`${i.id}:${i.prefix}`);
        });
      }
    }
    return s;
  },
  Ge = () => {
    Xe();
    const s = new We(De, Et);
    s.setCmpStatus(Q.LOADED),
      window.addEventListener("FidesInitialized", (e) => {
        const { experience: t } = window.Fides;
        if ((s.setSupportedAPIs(_t()), de(t) && !St(t, e.detail))) {
          Ve(e, s) && s.setApplicableSections([N.ID]),
            Me({ cmpApi: s, experience: t });
          const n = Le({ cmpApi: s, cookie: e.detail, region: t.region });
          n.length && s.setApplicableSections(n.map((i) => i.id)),
            s.setSignalStatus(B.READY);
        }
      }),
      window.addEventListener("FidesUIShown", () => {
        s.setSignalStatus(B.NOT_READY), s.setCmpDisplayStatus(k.VISIBLE);
        const { experience: e } = window.Fides;
        if (de(e)) {
          const t = Me({ cmpApi: s, experience: e });
          s.setApplicableSections(t.map((n) => n.id));
        }
      }),
      window.addEventListener("FidesModalClosed", (e) => {
        e.detail.extraDetails &&
          e.detail.extraDetails.saved === !1 &&
          (s.setCmpDisplayStatus(k.HIDDEN), s.setSignalStatus(B.READY));
      }),
      window.addEventListener("FidesUpdated", (e) => {
        var t, n;
        s.setCmpDisplayStatus(k.HIDDEN),
          Ve(e, s) &&
            (s.setApplicableSections([N.ID]), s.fireSectionChange("tcfeuv2"));
        const i = Le({
          cmpApi: s,
          cookie: e.detail,
          region:
            (n = (t = window.Fides.experience) == null ? void 0 : t.region) !=
            null
              ? n
              : "",
        });
        i.length &&
          (s.setApplicableSections(i.map((r) => r.id)),
          i.forEach((r) => {
            s.fireSectionChange(r.name);
          })),
          s.setSignalStatus(B.READY);
      });
  };
Ge();
export { Ge as initializeGppCmpApi };
