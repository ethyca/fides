(function (_, V) {
  typeof exports == "object" && typeof module < "u"
    ? V(exports)
    : typeof define == "function" && define.amd
    ? define(["exports"], V)
    : ((_ = typeof globalThis < "u" ? globalThis : _ || self),
      V((_.Fides = {})));
})(this, function (_) {
  "use strict";
  const V = (e) => {
      var n;
      const o = (n = window.dataLayer) != null ? n : [];
      window.dataLayer = o;
      const t = { consent: e.detail.consent };
      o.push({ event: e.type, Fides: t });
    },
    Ao = () => {
      var e;
      window.addEventListener("FidesInitialized", (n) => V(n)),
        window.addEventListener("FidesUpdated", (n) => V(n)),
        (e = window.Fides) != null &&
          e.initialized &&
          V({
            type: "FidesInitialized",
            detail: {
              consent: window.Fides.consent,
              fides_meta: window.Fides.fides_meta,
              identity: window.Fides.identity,
              tcf_consent: window.Fides.tcf_consent,
            },
          });
    },
    Fo = () => {
      if (window.fbq) return window.fbq;
      const e = {
        queue: [],
        loaded: !0,
        version: "2.0",
        push(...n) {
          const o = window.fbq;
          o.callMethod ? o.callMethod(...n) : o.queue.push(n);
        },
      };
      return (
        (window.fbq = Object.assign(e.push, e)),
        (window._fbq = window.fbq),
        window.fbq
      );
    },
    Lo = (e) => {
      const n = Fo();
      n("consent", e.consent ? "grant" : "revoke"),
        e.dataUse
          ? n("dataProcessingOptions", [])
          : n("dataProcessingOptions", ["LDU"], 1, 1e3);
    },
    Ke = (e) => {
      var n;
      if (!((n = window.Shopify) != null && n.customerPrivacy))
        throw Error("Fides could not access Shopify's customerPrivacy API");
      window.Shopify.customerPrivacy.setTrackingConsent(!!e.tracking, () => {});
    },
    jo = (e) => {
      if (!window.Shopify)
        throw Error(
          "Fides.shopify was called but Shopify is not present in the page."
        );
      if (window.Shopify.customerPrivacy) {
        Ke(e);
        return;
      }
      window.Shopify.loadFeatures(
        [{ name: "consent-tracking-api", version: "0.1" }],
        (n) => {
          if (n)
            throw Error("Fides could not load Shopify's consent-tracking-api");
          Ke(e);
        }
      );
    };
  let re;
  const Ro = new Uint8Array(16);
  function Do() {
    if (
      !re &&
      ((re =
        typeof crypto < "u" &&
        crypto.getRandomValues &&
        crypto.getRandomValues.bind(crypto)),
      !re)
    )
      throw new Error(
        "crypto.getRandomValues() not supported. See https://github.com/uuidjs/uuid#getrandomvalues-not-supported"
      );
    return re(Ro);
  }
  const C = [];
  for (let e = 0; e < 256; ++e) C.push((e + 256).toString(16).slice(1));
  function Mo(e, n = 0) {
    return (
      C[e[n + 0]] +
      C[e[n + 1]] +
      C[e[n + 2]] +
      C[e[n + 3]] +
      "-" +
      C[e[n + 4]] +
      C[e[n + 5]] +
      "-" +
      C[e[n + 6]] +
      C[e[n + 7]] +
      "-" +
      C[e[n + 8]] +
      C[e[n + 9]] +
      "-" +
      C[e[n + 10]] +
      C[e[n + 11]] +
      C[e[n + 12]] +
      C[e[n + 13]] +
      C[e[n + 14]] +
      C[e[n + 15]]
    ).toLowerCase();
  }
  var He = {
    randomUUID:
      typeof crypto < "u" &&
      crypto.randomUUID &&
      crypto.randomUUID.bind(crypto),
  };
  function Uo(e, n, o) {
    if (He.randomUUID && !n && !e) return He.randomUUID();
    e = e || {};
    const t = e.random || (e.rng || Do)();
    if (((t[6] = (t[6] & 15) | 64), (t[8] = (t[8] & 63) | 128), n)) {
      o = o || 0;
      for (let i = 0; i < 16; ++i) n[o + i] = t[i];
      return n;
    }
    return Mo(t);
  }
  /*! typescript-cookie v1.0.6 | MIT */ const Ye = (e) =>
      encodeURIComponent(e)
        .replace(/%(2[346B]|5E|60|7C)/g, decodeURIComponent)
        .replace(/[()]/g, escape),
    Ge = (e) =>
      encodeURIComponent(e).replace(
        /%(2[346BF]|3[AC-F]|40|5[BDE]|60|7[BCD])/g,
        decodeURIComponent
      ),
    we = decodeURIComponent,
    xe = (e) => (
      e[0] === '"' && (e = e.slice(1, -1)),
      e.replace(/(%[\dA-F]{2})+/gi, decodeURIComponent)
    );
  function zo(e) {
    return (
      (e = Object.assign({}, e)),
      typeof e.expires == "number" &&
        (e.expires = new Date(Date.now() + e.expires * 864e5)),
      e.expires != null && (e.expires = e.expires.toUTCString()),
      Object.entries(e)
        .filter(([n, o]) => o != null && o !== !1)
        .map(([n, o]) => (o === !0 ? `; ${n}` : `; ${n}=${o.split(";")[0]}`))
        .join("")
    );
  }
  function qe(e, n, o) {
    const t = /(?:^|; )([^=]*)=([^;]*)/g,
      i = {};
    let r;
    for (; (r = t.exec(document.cookie)) != null; )
      try {
        const l = o(r[1]);
        if (((i[l] = n(r[2], l)), e === l)) break;
      } catch {}
    return e != null ? i[e] : i;
  }
  const We = Object.freeze({
      decodeName: we,
      decodeValue: xe,
      encodeName: Ye,
      encodeValue: Ge,
    }),
    ke = Object.freeze({ path: "/" });
  function Ce(e, n, o = ke, { encodeValue: t = Ge, encodeName: i = Ye } = {}) {
    return (document.cookie = `${i(e)}=${t(n, e)}${zo(o)}`);
  }
  function Je(e, { decodeValue: n = xe, decodeName: o = we } = {}) {
    return qe(e, n, o);
  }
  function Vo({ decodeValue: e = xe, decodeName: n = we } = {}) {
    return qe(void 0, e, n);
  }
  function Ze(e, n = ke) {
    Ce(e, "", Object.assign({}, n, { expires: -1 }));
  }
  function Ee(e, n) {
    const o = {
        set: function (i, r, l) {
          return Ce(i, r, Object.assign({}, this.attributes, l), {
            encodeValue: this.converter.write,
          });
        },
        get: function (i) {
          if (arguments.length === 0) return Vo(this.converter.read);
          if (i != null) return Je(i, this.converter.read);
        },
        remove: function (i, r) {
          Ze(i, Object.assign({}, this.attributes, r));
        },
        withAttributes: function (i) {
          return Ee(this.converter, Object.assign({}, this.attributes, i));
        },
        withConverter: function (i) {
          return Ee(Object.assign({}, this.converter, i), this.attributes);
        },
      },
      t = {
        attributes: { value: Object.freeze(n) },
        converter: { value: Object.freeze(e) },
      };
    return Object.create(o, t);
  }
  Ee({ read: We.decodeValue, write: We.encodeValue }, ke);
  class se {
    constructor(n, o) {
      (this.notice = n), (this.consentPreference = o);
    }
  }
  (_.TCMobileDataVals = void 0),
    ((e) => {
      ((n) => ((n[(n._0 = 0)] = "_0"), (n[(n._1 = 1)] = "_1")))(
        e.IABTCFgdprApplies || (e.IABTCFgdprApplies = {})
      ),
        ((n) => ((n[(n._0 = 0)] = "_0"), (n[(n._1 = 1)] = "_1")))(
          e.IABTCFPurposeOneTreatment || (e.IABTCFPurposeOneTreatment = {})
        ),
        ((n) => ((n[(n._0 = 0)] = "_0"), (n[(n._1 = 1)] = "_1")))(
          e.IABTCFUseNonStandardTexts || (e.IABTCFUseNonStandardTexts = {})
        );
    })(_.TCMobileDataVals || (_.TCMobileDataVals = {}));
  var Xe = ((e) => (
      (e.FRONTEND = "frontend"),
      (e.SYSTEM_WIDE = "system_wide"),
      (e.NOT_APPLICABLE = "not_applicable"),
      e
    ))(Xe || {}),
    F = ((e) => (
      (e.OPT_IN = "opt_in"),
      (e.OPT_OUT = "opt_out"),
      (e.NOTICE_ONLY = "notice_only"),
      e
    ))(F || {}),
    T = ((e) => (
      (e.OPT_IN = "opt_in"),
      (e.OPT_OUT = "opt_out"),
      (e.ACKNOWLEDGE = "acknowledge"),
      e
    ))(T || {}),
    L = ((e) => (
      (e.OVERLAY = "overlay"),
      (e.PRIVACY_CENTER = "privacy_center"),
      (e.TCF_OVERLAY = "tcf_overlay"),
      e
    ))(L || {}),
    Qe = ((e) => (
      (e.ALWAYS_ENABLED = "always_enabled"),
      (e.ENABLED_WHERE_REQUIRED = "enabled_where_required"),
      (e.ALWAYS_DISABLED = "always_disabled"),
      e
    ))(Qe || {}),
    j = ((e) => (
      (e.PRIMARY = "primary"),
      (e.SECONDARY = "secondary"),
      (e.TERTIARY = "tertiary"),
      e
    ))(j || {}),
    B = ((e) => (
      (e.BUTTON = "button"),
      (e.REJECT = "reject"),
      (e.ACCEPT = "accept"),
      (e.SAVE = "save"),
      (e.DISMISS = "dismiss"),
      (e.GPC = "gpc"),
      (e.INDIVIDUAL_NOTICE = "individual_notice"),
      e
    ))(B || {}),
    en = ((e) => (
      (e.privacy_center = "privacy_center"),
      (e.overlay = "overlay"),
      (e.api = "api"),
      e
    ))(en || {}),
    G = ((e) => (
      (e.NONE = "none"),
      (e.APPLIED = "applied"),
      (e.OVERRIDDEN = "overridden"),
      e
    ))(G || {}),
    Z = ((e) => (
      (e.OVERLAY = "overlay"),
      (e.BANNER = "banner"),
      (e.PRIVACY_CENTER = "privacy_center"),
      (e.TCF_OVERLAY = "tcf_overlay"),
      (e.TCF_BANNER = "tcf_banner"),
      e
    ))(Z || {});
  const ae = (e, n) => !!Object.hasOwn(n.consent, e.notice_key),
    de = (e) =>
      !e || e === T.OPT_OUT ? !1 : e === T.OPT_IN ? !0 : e === T.ACKNOWLEDGE,
    X = (e, n) =>
      e ? (n === F.NOTICE_ONLY ? T.ACKNOWLEDGE : T.OPT_IN) : T.OPT_OUT,
    nn = (e, n) =>
      e === void 0
        ? !1
        : typeof e == "boolean"
        ? e
        : n.globalPrivacyControl === !0
        ? e.globalPrivacyControl
        : e.value,
    Oe = (e, n, o) =>
      e.consent_mechanism === F.NOTICE_ONLY
        ? !0
        : ae(e, o)
        ? !!o.consent[e.notice_key]
        : de(e.default_preference),
    Bo = /^\w{2,3}(-\w{2,3})?$/,
    Ko = [
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
    v = (e, ...n) => {
      e && console.log(...n);
    },
    q = (e) =>
      !e || typeof e != "object"
        ? !1
        : Object.keys(e).length === 0 || "id" in e,
    Pe = (e, n = !1) => (
      v(n, "constructing geolocation..."),
      e
        ? e.location && Bo.test(e.location)
          ? e.location.replace("-", "_").toLowerCase()
          : e.country && e.region
          ? `${e.country.toLowerCase()}_${e.region.toLowerCase()}`
          : (v(
              n,
              "cannot construct user location from provided geoLocation params..."
            ),
            null)
        : (v(
            n,
            "cannot construct user location since geoLocation is undefined or null"
          ),
          null)
    ),
    on = (e) => {
      if (
        (v(e.debug, "Validating Fides consent overlay options...", e),
        typeof e != "object")
      )
        return !1;
      if (!e.fidesApiUrl)
        return v(e.debug, "Invalid options: fidesApiUrl is required!"), !1;
      if (!e.privacyCenterUrl)
        return v(e.debug, "Invalid options: privacyCenterUrl is required!"), !1;
      try {
        new URL(e.privacyCenterUrl), new URL(e.fidesApiUrl);
      } catch {
        return (
          v(
            e.debug,
            "Invalid options: privacyCenterUrl or fidesApiUrl is an invalid URL!",
            e.privacyCenterUrl
          ),
          !1
        );
      }
      return !0;
    },
    tn = (e, n) =>
      q(e)
        ? e.component !== L.OVERLAY && e.component !== L.TCF_OVERLAY
          ? (v(
              n.debug,
              "No experience found with overlay component. Skipping overlay initialization."
            ),
            !1)
          : e.component === L.OVERLAY &&
            !(e.privacy_notices && e.privacy_notices.length > 0)
          ? (v(
              n.debug,
              "Privacy experience has no notices. Skipping overlay initialization."
            ),
            !1)
          : e.experience_config
          ? !0
          : (v(
              n.debug,
              "No experience config found with for experience. Skipping overlay initialization."
            ),
            !1)
        : (v(
            n.debug,
            "No relevant experience found. Skipping overlay initialization."
          ),
          !1),
    Ho = (e) => {
      var n;
      return (n = e.default_preference) != null ? n : T.OPT_OUT;
    },
    rn = (e, n) => {
      var o, t;
      return e.component === L.TCF_OVERLAY
        ? (o = e.meta) != null && o.version_hash
          ? e.meta.version_hash !== n.tcf_version_hash
          : !0
        : e?.privacy_notices == null || e.privacy_notices.length === 0
        ? !1
        : !((t = e.privacy_notices) != null && t.every((i) => ae(i, n)));
    },
    sn = (e) => {
      e[0] === "window" && e.shift();
      let n = window;
      for (; e.length > 0; ) {
        const o = e.shift();
        if (typeof o > "u" || typeof n[o] != "object") return;
        n = n[o];
      }
      return n;
    },
    an = ({ value: e, notice: n, consentContext: o }) =>
      !o.globalPrivacyControl ||
      !n.has_gpc_flag ||
      n.consent_mechanism === F.NOTICE_ONLY
        ? G.NONE
        : e
        ? G.OVERRIDDEN
        : G.APPLIED;
  var Yo = ((e) => (
      (e.CONSENT = "Consent"),
      (e.CONTRACT = "Contract"),
      (e.LEGAL_OBLIGATIONS = "Legal obligations"),
      (e.VITAL_INTERESTS = "Vital interests"),
      (e.PUBLIC_INTEREST = "Public interest"),
      (e.LEGITIMATE_INTERESTS = "Legitimate interests"),
      e
    ))(Yo || {}),
    $e = ((e) => (
      (e.CONSENT = "Consent"),
      (e.LEGITIMATE_INTERESTS = "Legitimate interests"),
      e
    ))($e || {});
  const Go = [
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
    qo = [
      {
        cookieKey: "system_consent_preferences",
        experienceKey: "tcf_system_consents",
      },
      {
        cookieKey: "system_legitimate_interests_preferences",
        experienceKey: "tcf_system_legitimate_interests",
      },
    ];
  Go.filter(
    ({ experienceKey: e }) =>
      e !== "tcf_features" && e !== "tcf_special_purposes"
  ).map((e) => e.experienceKey),
    $e.CONSENT,
    $e.LEGITIMATE_INTERESTS;
  var Wo = Object.defineProperty,
    Jo = Object.defineProperties,
    Zo = Object.getOwnPropertyDescriptors,
    dn = Object.getOwnPropertySymbols,
    Xo = Object.prototype.hasOwnProperty,
    Qo = Object.prototype.propertyIsEnumerable,
    ln = (e, n, o) =>
      n in e
        ? Wo(e, n, { enumerable: !0, configurable: !0, writable: !0, value: o })
        : (e[n] = o),
    W = (e, n) => {
      for (var o in n || (n = {})) Xo.call(n, o) && ln(e, o, n[o]);
      if (dn) for (var o of dn(n)) Qo.call(n, o) && ln(e, o, n[o]);
      return e;
    },
    le = (e, n) => Jo(e, Zo(n)),
    et = (e, n, o) =>
      new Promise((t, i) => {
        var r = (s) => {
            try {
              a(o.next(s));
            } catch (c) {
              i(c);
            }
          },
          l = (s) => {
            try {
              a(o.throw(s));
            } catch (c) {
              i(c);
            }
          },
          a = (s) =>
            s.done ? t(s.value) : Promise.resolve(s.value).then(r, l);
        a((o = o.apply(e, n)).next());
      });
  const Ne = "fides_consent",
    cn = 365,
    fn = {
      decodeName: decodeURIComponent,
      decodeValue: decodeURIComponent,
      encodeName: encodeURIComponent,
      encodeValue: encodeURIComponent,
    },
    pn = (e) => (e ? Object.values(e).some((n) => n !== void 0) : !1),
    un = () => Uo(),
    vn = (e) => {
      var n;
      return !((n = e.fides_meta) != null && n.updatedAt);
    },
    gn = (e) => {
      const n = new Date(),
        o = un();
      return {
        consent: e || {},
        identity: { fides_user_device_id: o },
        fides_meta: {
          version: "0.9.0",
          createdAt: n.toISOString(),
          updatedAt: "",
        },
        tcf_consent: {},
      };
    },
    Se = (e) => Je(e, fn),
    _n = (e, n = !1) => {
      const o = gn(e);
      if (typeof document > "u") return o;
      const t = Se(Ne);
      if (!t)
        return (
          v(
            n,
            "No existing Fides consent cookie found, returning defaults.",
            t
          ),
          o
        );
      try {
        let i;
        const r = JSON.parse(t);
        "consent" in r && "fides_meta" in r
          ? (i = r)
          : (i = le(W({}, o), { consent: r }));
        const l = W(W({}, e), i.consent);
        return (
          (i.consent = l),
          v(
            n,
            "Applied existing consent to data from existing Fides consent cookie.",
            JSON.stringify(i)
          ),
          i
        );
      } catch (i) {
        return v(n, "Unable to read consent cookie: invalid JSON.", i), o;
      }
    },
    yn = (e) => {
      if (typeof document > "u") return;
      const n = new Date().toISOString();
      e.fides_meta.updatedAt = n;
      const o = window.location.hostname.split(".").slice(-2).join(".");
      Ce(Ne, JSON.stringify(e), { path: "/", domain: o, expires: cn }, fn);
    },
    Te = ({ experience: e, cookie: n, debug: o }) => {
      var t;
      const i =
        (t = e.privacy_notices) == null
          ? void 0
          : t.map((r) => {
              const l = Object.hasOwn(n.consent, r.notice_key)
                ? X(!!n.consent[r.notice_key], r.consent_mechanism)
                : void 0;
              return le(W({}, r), { current_preference: l });
            });
      return (
        o &&
          v(
            o,
            "Returning updated pre-fetched experience with user consent.",
            e
          ),
        le(W({}, e), { privacy_notices: i })
      );
    },
    nt = (e) => {
      const n = {};
      return (
        qo.forEach(({ cookieKey: o }) => {
          var t;
          const i = (t = e[o]) != null ? t : [];
          n[o] = Object.fromEntries(i.map((r) => [r.id, de(r.preference)]));
        }),
        n
      );
    },
    bn = (e, n, o) => {
      const t = {};
      return (
        e?.options.forEach(({ cookieKeys: i, default: r }) => {
          if (r === void 0) return;
          const l = nn(r, n);
          i.forEach((a) => {
            const s = t[a];
            if (s === void 0) {
              t[a] = l;
              return;
            }
            t[a] = s && l;
          });
        }),
        v(o, "Returning defaults for legacy config.", t),
        t
      );
    },
    mn = (e) => {
      e.forEach((n) => {
        var o;
        Ze(n.name, { path: (o = n.path) != null ? o : "/", domain: n.domain });
      });
    },
    Ie = (e, n) =>
      et(void 0, null, function* () {
        const o = new Map(
            n.map(({ notice: i, consentPreference: r }) => [
              i.notice_key,
              de(r),
            ])
          ),
          t = Object.fromEntries(o);
        return le(W({}, e), { consent: t });
      });
  var ot = Object.defineProperty,
    tt = Object.defineProperties,
    it = Object.getOwnPropertyDescriptors,
    hn = Object.getOwnPropertySymbols,
    rt = Object.prototype.hasOwnProperty,
    st = Object.prototype.propertyIsEnumerable,
    wn = (e, n, o) =>
      n in e
        ? ot(e, n, { enumerable: !0, configurable: !0, writable: !0, value: o })
        : (e[n] = o),
    at = (e, n) => {
      for (var o in n || (n = {})) rt.call(n, o) && wn(e, o, n[o]);
      if (hn) for (var o of hn(n)) st.call(n, o) && wn(e, o, n[o]);
      return e;
    },
    dt = (e, n) => tt(e, it(n));
  const M = (e, n, o, t) => {
      if (typeof window < "u" && typeof CustomEvent < "u") {
        const i = new CustomEvent(e, {
          detail: dt(at({}, n), { debug: o, extraDetails: t }),
        });
        v(
          o,
          `Dispatching event type ${e} ${
            t != null && t.servingComponent ? `from ${t.servingComponent} ` : ""
          }with cookie ${JSON.stringify(n)} ${
            t != null && t.consentMethod
              ? `using consent method ${t.consentMethod} `
              : ""
          }`
        ),
          window.dispatchEvent(i);
      }
    },
    lt = () => {
      var e;
      if (window.Fides.options.tcfEnabled) return !1;
      if (
        typeof ((e = window.navigator) == null
          ? void 0
          : e.globalPrivacyControl) == "boolean"
      )
        return window.navigator.globalPrivacyControl;
      const n = new URL(window.location.href).searchParams.get(
        "globalPrivacyControl"
      );
      if (n === "true") return !0;
      if (n === "false") return !1;
    },
    U = () => (typeof window > "u" ? {} : { globalPrivacyControl: lt() });
  var ct = Object.defineProperty,
    ft = Object.defineProperties,
    pt = Object.getOwnPropertyDescriptors,
    xn = Object.getOwnPropertySymbols,
    ut = Object.prototype.hasOwnProperty,
    vt = Object.prototype.propertyIsEnumerable,
    kn = (e, n, o) =>
      n in e
        ? ct(e, n, { enumerable: !0, configurable: !0, writable: !0, value: o })
        : (e[n] = o),
    Cn = (e, n) => {
      for (var o in n || (n = {})) ut.call(n, o) && kn(e, o, n[o]);
      if (xn) for (var o of xn(n)) vt.call(n, o) && kn(e, o, n[o]);
      return e;
    },
    En = (e, n) => ft(e, pt(n)),
    Ae = (e, n, o) =>
      new Promise((t, i) => {
        var r = (s) => {
            try {
              a(o.next(s));
            } catch (c) {
              i(c);
            }
          },
          l = (s) => {
            try {
              a(o.throw(s));
            } catch (c) {
              i(c);
            }
          },
          a = (s) =>
            s.done ? t(s.value) : Promise.resolve(s.value).then(r, l);
        a((o = o.apply(e, n)).next());
      }),
    On = ((e) => (
      (e.PRIVACY_EXPERIENCE = "/privacy-experience"),
      (e.PRIVACY_PREFERENCES = "/privacy-preferences"),
      (e.NOTICES_SERVED = "/notices-served"),
      e
    ))(On || {});
  const Pn = (e, n, o, t) =>
      Ae(void 0, null, function* () {
        var i;
        if (
          (v(o, `Fetching experience in location: ${e}`),
          t != null && t.getPrivacyExperienceFn)
        ) {
          v(o, "Calling custom fetch experience fn");
          try {
            return yield t.getPrivacyExperienceFn(e, null);
          } catch (s) {
            return (
              v(
                o,
                "Error fetching experience from custom API, returning {}. Error: ",
                s
              ),
              {}
            );
          }
        }
        v(o, "Calling Fides GET experience API");
        const r = {
          method: "GET",
          mode: "cors",
          headers: [["Unescape-Safestr", "true"]],
        };
        let l = {
          show_disabled: "false",
          region: e,
          component: L.OVERLAY,
          has_notices: "true",
          has_config: "true",
          systems_applicable: "true",
          include_gvl: "true",
          include_meta: "true",
        };
        l = new URLSearchParams(l);
        const a = yield fetch(`${n}/privacy-experience?${l}`, r);
        if (!a.ok)
          return (
            v(
              o,
              "Error getting experience from Fides API, returning {}. Response:",
              a
            ),
            {}
          );
        try {
          const s = yield a.json(),
            c = (i = s.items && s.items[0]) != null ? i : {};
          return (
            v(o, "Got experience response from Fides API, returning: ", c), c
          );
        } catch {
          return (
            v(
              o,
              "Error parsing experience response body from Fides API, returning {}. Response:",
              a
            ),
            {}
          );
        }
      }),
    $n = {
      method: "PATCH",
      mode: "cors",
      headers: { "Content-Type": "application/json" },
    },
    Nn = (e, n, o, t, i) =>
      Ae(void 0, null, function* () {
        var r;
        if (
          (v(o.debug, "Saving user consent preference...", n),
          (r = o.apiOptions) != null && r.savePreferencesFn)
        ) {
          v(o.debug, "Calling custom save preferences fn");
          try {
            yield o.apiOptions.savePreferencesFn(
              e,
              t.consent,
              t.fides_string,
              i
            );
          } catch (s) {
            return (
              v(
                o.debug,
                "Error saving preferences to custom API, continuing. Error: ",
                s
              ),
              Promise.reject(s)
            );
          }
          return Promise.resolve();
        }
        v(o.debug, "Calling Fides save preferences API");
        const l = En(Cn({}, $n), { body: JSON.stringify(n) }),
          a = yield fetch(`${o.fidesApiUrl}/privacy-preferences`, l);
        return (
          a.ok ||
            v(
              o.debug,
              "Error patching user preference Fides API. Response:",
              a
            ),
          Promise.resolve()
        );
      }),
    Sn = (e) =>
      Ae(void 0, [e], function* ({ request: n, options: o }) {
        var t;
        if (
          (v(o.debug, "Saving that notices were served..."),
          (t = o.apiOptions) != null && t.patchNoticesServedFn)
        ) {
          v(o.debug, "Calling custom patch notices served fn");
          try {
            return yield o.apiOptions.patchNoticesServedFn(n);
          } catch (l) {
            return (
              v(
                o.debug,
                "Error patching notices served to custom API, continuing. Error: ",
                l
              ),
              null
            );
          }
        }
        v(o.debug, "Calling Fides patch notices served API");
        const i = En(Cn({}, $n), { body: JSON.stringify(n) }),
          r = yield fetch(`${o.fidesApiUrl}/notices-served`, i);
        return r.ok
          ? r.json()
          : (v(o.debug, "Error patching notices served. Response:", r), null);
      });
  var gt = (e, n, o) =>
    new Promise((t, i) => {
      var r = (s) => {
          try {
            a(o.next(s));
          } catch (c) {
            i(c);
          }
        },
        l = (s) => {
          try {
            a(o.throw(s));
          } catch (c) {
            i(c);
          }
        },
        a = (s) => (s.done ? t(s.value) : Promise.resolve(s.value).then(r, l));
      a((o = o.apply(e, n)).next());
    });
  const Tn = (e, n, o = !1) =>
    gt(void 0, null, function* () {
      if ((v(o, "Running getLocation..."), !e))
        return (
          v(
            o,
            "User location could not be retrieved because geolocation is disabled."
          ),
          null
        );
      if (!n)
        return (
          v(
            o,
            "Location cannot be found due to no configured geoLocationApiUrl."
          ),
          null
        );
      v(o, `Calling geolocation API: GET ${n}...`);
      const t = yield fetch(n, { mode: "cors" });
      if (!t.ok)
        return (
          v(
            o,
            "Error getting location from geolocation API, returning {}. Response:",
            t
          ),
          null
        );
      try {
        const i = yield t.json();
        return (
          v(o, "Got location response from geolocation API, returning:", i), i
        );
      } catch {
        return (
          v(
            o,
            "Error parsing response body from geolocation API, returning {}. Response:",
            t
          ),
          null
        );
      }
    });
  var _t = Object.defineProperty,
    In = Object.getOwnPropertySymbols,
    yt = Object.prototype.hasOwnProperty,
    bt = Object.prototype.propertyIsEnumerable,
    An = (e, n, o) =>
      n in e
        ? _t(e, n, { enumerable: !0, configurable: !0, writable: !0, value: o })
        : (e[n] = o),
    mt = (e, n) => {
      for (var o in n || (n = {})) yt.call(n, o) && An(e, o, n[o]);
      if (In) for (var o of In(n)) bt.call(n, o) && An(e, o, n[o]);
      return e;
    },
    Fn = (e, n, o) =>
      new Promise((t, i) => {
        var r = (s) => {
            try {
              a(o.next(s));
            } catch (c) {
              i(c);
            }
          },
          l = (s) => {
            try {
              a(o.throw(s));
            } catch (c) {
              i(c);
            }
          },
          a = (s) =>
            s.done ? t(s.value) : Promise.resolve(s.value).then(r, l);
        a((o = o.apply(e, n)).next());
      });
  function ht(e, n, o, t, i, r, l, a) {
    return Fn(this, null, function* () {
      v(e.debug, "Saving preferences to Fides API");
      const s = i?.map((d) => ({
          privacy_notice_history_id: d.notice.privacy_notice_history_id,
          preference: d.consentPreference,
        })),
        c = mt(
          {
            browser_identity: n.identity,
            preferences: s,
            privacy_experience_id: o.id,
            user_geography: l,
            method: t,
            served_notice_history_id: a,
          },
          r ?? []
        );
      yield Nn(t, c, e, n, o);
    });
  }
  const Ln = (e) =>
    Fn(
      void 0,
      [e],
      function* ({
        consentPreferencesToSave: n,
        experience: o,
        consentMethod: t,
        options: i,
        userLocationString: r,
        cookie: l,
        servedNoticeHistoryId: a,
        tcf: s,
        updateCookie: c,
      }) {
        if (i.fidesPreviewMode) return;
        const d = { consentMethod: t },
          y = yield c(l);
        if (
          (Object.assign(l, y),
          Object.assign(l.fides_meta, d),
          v(i.debug, "Updating window.Fides"),
          (window.Fides.consent = l.consent),
          (window.Fides.fides_string = l.fides_string),
          (window.Fides.tcf_consent = l.tcf_consent),
          !i.fidesDisableSaveApi)
        )
          try {
            yield ht(i, l, o, t, n, s, r, a);
          } catch (p) {
            v(
              i.debug,
              "Error saving updated preferences to API, continuing. Error: ",
              p
            );
          }
        v(i.debug, "Saving preferences to cookie"),
          yn(l),
          n &&
            n
              .filter((p) => p.consentPreference === T.OPT_OUT)
              .forEach((p) => {
                mn(p.notice.cookies);
              }),
          M("FidesUpdated", l, i.debug, d);
      }
    );
  var Fe = (e, n, o) =>
    new Promise((t, i) => {
      var r = (s) => {
          try {
            a(o.next(s));
          } catch (c) {
            i(c);
          }
        },
        l = (s) => {
          try {
            a(o.throw(s));
          } catch (c) {
            i(c);
          }
        },
        a = (s) => (s.done ? t(s.value) : Promise.resolve(s.value).then(r, l));
      a((o = o.apply(e, n)).next());
    });
  const wt = "fides-embed-container",
    xt = "fides-overlay",
    jn = (e) =>
      Fe(
        void 0,
        [e],
        function* ({
          experience: n,
          fidesRegionString: o,
          cookie: t,
          options: i,
          renderOverlay: r,
        }) {
          v(i.debug, "Initializing Fides consent overlays...");
          function l() {
            return Fe(this, null, function* () {
              try {
                v(
                  i.debug,
                  "Rendering Fides overlay CSS & HTML into the DOM..."
                );
                let a;
                if (i.fidesEmbed) {
                  if (((a = document.getElementById(wt)), !a))
                    throw new Error(
                      "Element with id fides-embed-container could not be found."
                    );
                } else {
                  const s = i.overlayParentId || xt;
                  (a = document.getElementById(s)),
                    a ||
                      (v(
                        i.debug,
                        `Parent element not found (#${s}), creating and appending to body...`
                      ),
                      (a = document.createElement("div")),
                      (a.id = s),
                      document.body.prepend(a));
                }
                return (
                  (n.component === L.OVERLAY ||
                    n.component === L.TCF_OVERLAY) &&
                    (r(
                      {
                        experience: n,
                        fidesRegionString: o,
                        cookie: t,
                        options: i,
                      },
                      a
                    ),
                    v(i.debug, "Fides overlay is now showing!")),
                  yield Promise.resolve()
                );
              } catch (a) {
                return v(i.debug, a), Promise.reject(a);
              }
            });
          }
          return (
            document?.readyState !== "complete"
              ? (v(i.debug, "DOM not loaded, adding event listener"),
                document.addEventListener("readystatechange", () =>
                  Fe(void 0, null, function* () {
                    document.readyState === "complete" &&
                      (v(i.debug, "DOM fully loaded and parsed"), yield l());
                  })
                ))
              : yield l(),
            Promise.resolve()
          );
        }
      );
  var kt = (e, n, o) =>
    new Promise((t, i) => {
      var r = (s) => {
          try {
            a(o.next(s));
          } catch (c) {
            i(c);
          }
        },
        l = (s) => {
          try {
            a(o.throw(s));
          } catch (c) {
            i(c);
          }
        },
        a = (s) => (s.done ? t(s.value) : Promise.resolve(s.value).then(r, l));
      a((o = o.apply(e, n)).next());
    });
  const Ct = (e) =>
    kt(void 0, [e], function* ({ options: n, experience: o }) {
      var t;
      if ((t = o?.gpp_settings) != null && t.enabled)
        try {
          yield import(`${n.fidesJsBaseUrl}/fides-ext-gpp.js`);
        } catch (i) {
          console.error("Unable to import GPP extension", i);
        }
    });
  var Rn = (e, n, o) =>
    new Promise((t, i) => {
      var r = (s) => {
          try {
            a(o.next(s));
          } catch (c) {
            i(c);
          }
        },
        l = (s) => {
          try {
            a(o.throw(s));
          } catch (c) {
            i(c);
          }
        },
        a = (s) => (s.done ? t(s.value) : Promise.resolve(s.value).then(r, l));
      a((o = o.apply(e, n)).next());
    });
  const Et = (e, n) =>
      Rn(void 0, null, function* () {
        return (
          Pe(e) ||
          Pe(yield Tn(n.isGeolocationEnabled, n.geolocationApiUrl, n.debug))
        );
      }),
    Ot = ({
      cookie: e,
      fidesRegionString: n,
      effectiveExperience: o,
      fidesOptions: t,
    }) => {
      if (!o || !o.privacy_notices) return !1;
      const i = U();
      if (!i.globalPrivacyControl) return !1;
      let r = !1;
      const l = o.privacy_notices.map((a) => {
        const s = ae(a, e);
        return a.has_gpc_flag && !s && a.consent_mechanism !== F.NOTICE_ONLY
          ? ((r = !0), new se(a, X(!1, a.consent_mechanism)))
          : new se(a, X(Oe(a, i, e), a.consent_mechanism));
      });
      return r
        ? (Ln({
            consentPreferencesToSave: l,
            experience: o,
            consentMethod: B.GPC,
            options: t,
            userLocationString: n || void 0,
            cookie: e,
            updateCookie: (a) => Ie(a, l),
          }),
          !0)
        : !1;
    },
    Pt = (e) => {
      const n = {};
      if (typeof window < "u") {
        const o = new URLSearchParams(window.location.search),
          t =
            e.options.customOptionsPath &&
            e.options.customOptionsPath.split("."),
          i = t && t.length >= 0 ? sn(t) : window.fides_overrides;
        Ko.forEach(
          ({
            fidesOption: r,
            fidesOptionType: l,
            fidesOverrideKey: a,
            validationRegex: s,
          }) => {
            const c = o.get(a),
              d = i ? i[a] : void 0,
              y = Se(a),
              p = c || d || y;
            p &&
              s.test(p.toString()) &&
              (n[r] = l === "string" ? p : JSON.parse(p.toString()));
          }
        );
      }
      return n;
    },
    $t = ({ consent: e, options: n }) => {
      const o = U(),
        t = bn(e, o, n.debug);
      return _n(t, n.debug);
    },
    Nt = ({
      cookie: e,
      experience: n,
      geolocation: o,
      options: t,
      updateExperienceFromCookieConsent: i,
    }) => {
      if (vn(e) && !t.fidesString) return null;
      let r = n;
      return (
        q(n) && (r = i({ experience: n, cookie: e, debug: t.debug })),
        {
          consent: e.consent,
          fides_meta: e.fides_meta,
          identity: e.identity,
          experience: r,
          tcf_consent: e.tcf_consent,
          fides_string: e.fides_string,
          geolocation: o,
          options: t,
          initialized: !0,
        }
      );
    },
    St = (e) =>
      Rn(
        void 0,
        [e],
        function* ({
          cookie: n,
          options: o,
          experience: t,
          geolocation: i,
          renderOverlay: r,
          updateExperience: l,
        }) {
          let a = o.isOverlayEnabled,
            s = t,
            c = null;
          if (a) {
            on(o) ||
              (v(
                o.debug,
                "Invalid overlay options. Skipping overlay initialization.",
                o
              ),
              (a = !1)),
              (c = yield Et(i, o));
            let d = !1;
            if (
              (c
                ? q(s) ||
                  ((d = !0),
                  (s = yield Pn(c, o.fidesApiUrl, o.debug, o.apiOptions)))
                : (v(
                    o.debug,
                    "User location could not be obtained. Skipping overlay initialization."
                  ),
                  (a = !1)),
              q(s) && tn(s, o))
            ) {
              a &&
                q(s) &&
                Ot({
                  cookie: n,
                  fidesRegionString: c,
                  effectiveExperience: s,
                  fidesOptions: o,
                });
              const y = yield l({
                cookie: n,
                experience: s,
                debug: o.debug,
                isExperienceClientSideFetched: d,
              });
              v(o.debug, "Updated experience", y),
                Object.assign(s, y),
                a &&
                  (yield jn({
                    experience: s,
                    fidesRegionString: c,
                    cookie: n,
                    options: o,
                    renderOverlay: r,
                  }).catch(() => {}));
            }
          }
          return (
            yield Ct({ options: o, experience: s }),
            {
              consent: n.consent,
              fides_meta: n.fides_meta,
              identity: n.identity,
              fides_string: n.fides_string,
              tcf_consent: n.tcf_consent,
              experience: s,
              geolocation: i,
              options: o,
              initialized: !0,
            }
          );
        }
      );
  var ce,
    m,
    Dn,
    K,
    Mn,
    Un,
    Le,
    fe = {},
    zn = [],
    Tt = /acit|ex(?:s|g|n|p|$)|rph|grid|ows|mnc|ntw|ine[ch]|zoo|^ord|itera/i,
    je = Array.isArray;
  function z(e, n) {
    for (var o in n) e[o] = n[o];
    return e;
  }
  function Vn(e) {
    var n = e.parentNode;
    n && n.removeChild(e);
  }
  function f(e, n, o) {
    var t,
      i,
      r,
      l = {};
    for (r in n)
      r == "key" ? (t = n[r]) : r == "ref" ? (i = n[r]) : (l[r] = n[r]);
    if (
      (arguments.length > 2 &&
        (l.children = arguments.length > 3 ? ce.call(arguments, 2) : o),
      typeof e == "function" && e.defaultProps != null)
    )
      for (r in e.defaultProps) l[r] === void 0 && (l[r] = e.defaultProps[r]);
    return pe(e, l, t, i, null);
  }
  function pe(e, n, o, t, i) {
    var r = {
      type: e,
      props: n,
      key: o,
      ref: t,
      __k: null,
      __: null,
      __b: 0,
      __e: null,
      __d: void 0,
      __c: null,
      __h: null,
      constructor: void 0,
      __v: i ?? ++Dn,
    };
    return i == null && m.vnode != null && m.vnode(r), r;
  }
  function H(e) {
    return e.children;
  }
  function ue(e, n) {
    (this.props = e), (this.context = n);
  }
  function Q(e, n) {
    if (n == null) return e.__ ? Q(e.__, e.__.__k.indexOf(e) + 1) : null;
    for (var o; n < e.__k.length; n++)
      if ((o = e.__k[n]) != null && o.__e != null) return o.__e;
    return typeof e.type == "function" ? Q(e) : null;
  }
  function Bn(e) {
    var n, o;
    if ((e = e.__) != null && e.__c != null) {
      for (e.__e = e.__c.base = null, n = 0; n < e.__k.length; n++)
        if ((o = e.__k[n]) != null && o.__e != null) {
          e.__e = e.__c.base = o.__e;
          break;
        }
      return Bn(e);
    }
  }
  function Kn(e) {
    ((!e.__d && (e.__d = !0) && K.push(e) && !ve.__r++) ||
      Mn !== m.debounceRendering) &&
      ((Mn = m.debounceRendering) || Un)(ve);
  }
  function ve() {
    var e, n, o, t, i, r, l, a;
    for (K.sort(Le); (e = K.shift()); )
      e.__d &&
        ((n = K.length),
        (t = void 0),
        (i = void 0),
        (l = (r = (o = e).__v).__e),
        (a = o.__P) &&
          ((t = []),
          ((i = z({}, r)).__v = r.__v + 1),
          Re(
            a,
            r,
            i,
            o.__n,
            a.ownerSVGElement !== void 0,
            r.__h != null ? [l] : null,
            t,
            l ?? Q(r),
            r.__h
          ),
          Xn(t, r),
          r.__e != l && Bn(r)),
        K.length > n && K.sort(Le));
    ve.__r = 0;
  }
  function Hn(e, n, o, t, i, r, l, a, s, c) {
    var d,
      y,
      p,
      u,
      g,
      O,
      b,
      h = (t && t.__k) || zn,
      w = h.length;
    for (o.__k = [], d = 0; d < n.length; d++)
      if (
        (u = o.__k[d] =
          (u = n[d]) == null || typeof u == "boolean" || typeof u == "function"
            ? null
            : typeof u == "string" ||
              typeof u == "number" ||
              typeof u == "bigint"
            ? pe(null, u, null, null, u)
            : je(u)
            ? pe(H, { children: u }, null, null, null)
            : u.__b > 0
            ? pe(u.type, u.props, u.key, u.ref ? u.ref : null, u.__v)
            : u) != null
      ) {
        if (
          ((u.__ = o),
          (u.__b = o.__b + 1),
          (p = h[d]) === null || (p && u.key == p.key && u.type === p.type))
        )
          h[d] = void 0;
        else
          for (y = 0; y < w; y++) {
            if ((p = h[y]) && u.key == p.key && u.type === p.type) {
              h[y] = void 0;
              break;
            }
            p = null;
          }
        Re(e, u, (p = p || fe), i, r, l, a, s, c),
          (g = u.__e),
          (y = u.ref) &&
            p.ref != y &&
            (b || (b = []),
            p.ref && b.push(p.ref, null, u),
            b.push(y, u.__c || g, u)),
          g != null
            ? (O == null && (O = g),
              typeof u.type == "function" && u.__k === p.__k
                ? (u.__d = s = Yn(u, s, e))
                : (s = Gn(e, u, p, h, g, s)),
              typeof o.type == "function" && (o.__d = s))
            : s && p.__e == s && s.parentNode != e && (s = Q(p));
      }
    for (o.__e = O, d = w; d--; )
      h[d] != null &&
        (typeof o.type == "function" &&
          h[d].__e != null &&
          h[d].__e == o.__d &&
          (o.__d = qn(t).nextSibling),
        eo(h[d], h[d]));
    if (b) for (d = 0; d < b.length; d++) Qn(b[d], b[++d], b[++d]);
  }
  function Yn(e, n, o) {
    for (var t, i = e.__k, r = 0; i && r < i.length; r++)
      (t = i[r]) &&
        ((t.__ = e),
        (n =
          typeof t.type == "function"
            ? Yn(t, n, o)
            : Gn(o, t, t, i, t.__e, n)));
    return n;
  }
  function Gn(e, n, o, t, i, r) {
    var l, a, s;
    if (n.__d !== void 0) (l = n.__d), (n.__d = void 0);
    else if (o == null || i != r || i.parentNode == null)
      e: if (r == null || r.parentNode !== e) e.appendChild(i), (l = null);
      else {
        for (a = r, s = 0; (a = a.nextSibling) && s < t.length; s += 1)
          if (a == i) break e;
        e.insertBefore(i, r), (l = r);
      }
    return l !== void 0 ? l : i.nextSibling;
  }
  function qn(e) {
    var n, o, t;
    if (e.type == null || typeof e.type == "string") return e.__e;
    if (e.__k) {
      for (n = e.__k.length - 1; n >= 0; n--)
        if ((o = e.__k[n]) && (t = qn(o))) return t;
    }
    return null;
  }
  function It(e, n, o, t, i) {
    var r;
    for (r in o)
      r === "children" || r === "key" || r in n || ge(e, r, null, o[r], t);
    for (r in n)
      (i && typeof n[r] != "function") ||
        r === "children" ||
        r === "key" ||
        r === "value" ||
        r === "checked" ||
        o[r] === n[r] ||
        ge(e, r, n[r], o[r], t);
  }
  function Wn(e, n, o) {
    n[0] === "-"
      ? e.setProperty(n, o ?? "")
      : (e[n] =
          o == null ? "" : typeof o != "number" || Tt.test(n) ? o : o + "px");
  }
  function ge(e, n, o, t, i) {
    var r;
    e: if (n === "style")
      if (typeof o == "string") e.style.cssText = o;
      else {
        if ((typeof t == "string" && (e.style.cssText = t = ""), t))
          for (n in t) (o && n in o) || Wn(e.style, n, "");
        if (o) for (n in o) (t && o[n] === t[n]) || Wn(e.style, n, o[n]);
      }
    else if (n[0] === "o" && n[1] === "n")
      (r = n !== (n = n.replace(/Capture$/, ""))),
        (n = n.toLowerCase() in e ? n.toLowerCase().slice(2) : n.slice(2)),
        e.l || (e.l = {}),
        (e.l[n + r] = o),
        o
          ? t || e.addEventListener(n, r ? Zn : Jn, r)
          : e.removeEventListener(n, r ? Zn : Jn, r);
    else if (n !== "dangerouslySetInnerHTML") {
      if (i) n = n.replace(/xlink(H|:h)/, "h").replace(/sName$/, "s");
      else if (
        n !== "width" &&
        n !== "height" &&
        n !== "href" &&
        n !== "list" &&
        n !== "form" &&
        n !== "tabIndex" &&
        n !== "download" &&
        n !== "rowSpan" &&
        n !== "colSpan" &&
        n in e
      )
        try {
          e[n] = o ?? "";
          break e;
        } catch {}
      typeof o == "function" ||
        (o == null || (o === !1 && n[4] !== "-")
          ? e.removeAttribute(n)
          : e.setAttribute(n, o));
    }
  }
  function Jn(e) {
    return this.l[e.type + !1](m.event ? m.event(e) : e);
  }
  function Zn(e) {
    return this.l[e.type + !0](m.event ? m.event(e) : e);
  }
  function Re(e, n, o, t, i, r, l, a, s) {
    var c,
      d,
      y,
      p,
      u,
      g,
      O,
      b,
      h,
      w,
      k,
      E,
      I,
      $,
      A,
      N = n.type;
    if (n.constructor !== void 0) return null;
    o.__h != null &&
      ((s = o.__h), (a = n.__e = o.__e), (n.__h = null), (r = [a])),
      (c = m.__b) && c(n);
    try {
      e: if (typeof N == "function") {
        if (
          ((b = n.props),
          (h = (c = N.contextType) && t[c.__c]),
          (w = c ? (h ? h.props.value : c.__) : t),
          o.__c
            ? (O = (d = n.__c = o.__c).__ = d.__E)
            : ("prototype" in N && N.prototype.render
                ? (n.__c = d = new N(b, w))
                : ((n.__c = d = new ue(b, w)),
                  (d.constructor = N),
                  (d.render = Ft)),
              h && h.sub(d),
              (d.props = b),
              d.state || (d.state = {}),
              (d.context = w),
              (d.__n = t),
              (y = d.__d = !0),
              (d.__h = []),
              (d._sb = [])),
          d.__s == null && (d.__s = d.state),
          N.getDerivedStateFromProps != null &&
            (d.__s == d.state && (d.__s = z({}, d.__s)),
            z(d.__s, N.getDerivedStateFromProps(b, d.__s))),
          (p = d.props),
          (u = d.state),
          (d.__v = n),
          y)
        )
          N.getDerivedStateFromProps == null &&
            d.componentWillMount != null &&
            d.componentWillMount(),
            d.componentDidMount != null && d.__h.push(d.componentDidMount);
        else {
          if (
            (N.getDerivedStateFromProps == null &&
              b !== p &&
              d.componentWillReceiveProps != null &&
              d.componentWillReceiveProps(b, w),
            (!d.__e &&
              d.shouldComponentUpdate != null &&
              d.shouldComponentUpdate(b, d.__s, w) === !1) ||
              n.__v === o.__v)
          ) {
            for (
              n.__v !== o.__v &&
                ((d.props = b), (d.state = d.__s), (d.__d = !1)),
                d.__e = !1,
                n.__e = o.__e,
                n.__k = o.__k,
                n.__k.forEach(function (he) {
                  he && (he.__ = n);
                }),
                k = 0;
              k < d._sb.length;
              k++
            )
              d.__h.push(d._sb[k]);
            (d._sb = []), d.__h.length && l.push(d);
            break e;
          }
          d.componentWillUpdate != null && d.componentWillUpdate(b, d.__s, w),
            d.componentDidUpdate != null &&
              d.__h.push(function () {
                d.componentDidUpdate(p, u, g);
              });
        }
        if (
          ((d.context = w),
          (d.props = b),
          (d.__P = e),
          (E = m.__r),
          (I = 0),
          "prototype" in N && N.prototype.render)
        ) {
          for (
            d.state = d.__s,
              d.__d = !1,
              E && E(n),
              c = d.render(d.props, d.state, d.context),
              $ = 0;
            $ < d._sb.length;
            $++
          )
            d.__h.push(d._sb[$]);
          d._sb = [];
        } else
          do
            (d.__d = !1),
              E && E(n),
              (c = d.render(d.props, d.state, d.context)),
              (d.state = d.__s);
          while (d.__d && ++I < 25);
        (d.state = d.__s),
          d.getChildContext != null && (t = z(z({}, t), d.getChildContext())),
          y ||
            d.getSnapshotBeforeUpdate == null ||
            (g = d.getSnapshotBeforeUpdate(p, u)),
          Hn(
            e,
            je(
              (A =
                c != null && c.type === H && c.key == null
                  ? c.props.children
                  : c)
            )
              ? A
              : [A],
            n,
            o,
            t,
            i,
            r,
            l,
            a,
            s
          ),
          (d.base = n.__e),
          (n.__h = null),
          d.__h.length && l.push(d),
          O && (d.__E = d.__ = null),
          (d.__e = !1);
      } else r == null && n.__v === o.__v ? ((n.__k = o.__k), (n.__e = o.__e)) : (n.__e = At(o.__e, n, o, t, i, r, l, s));
      (c = m.diffed) && c(n);
    } catch (he) {
      (n.__v = null),
        (s || r != null) &&
          ((n.__e = a), (n.__h = !!s), (r[r.indexOf(a)] = null)),
        m.__e(he, n, o);
    }
  }
  function Xn(e, n) {
    m.__c && m.__c(n, e),
      e.some(function (o) {
        try {
          (e = o.__h),
            (o.__h = []),
            e.some(function (t) {
              t.call(o);
            });
        } catch (t) {
          m.__e(t, o.__v);
        }
      });
  }
  function At(e, n, o, t, i, r, l, a) {
    var s,
      c,
      d,
      y = o.props,
      p = n.props,
      u = n.type,
      g = 0;
    if ((u === "svg" && (i = !0), r != null)) {
      for (; g < r.length; g++)
        if (
          (s = r[g]) &&
          "setAttribute" in s == !!u &&
          (u ? s.localName === u : s.nodeType === 3)
        ) {
          (e = s), (r[g] = null);
          break;
        }
    }
    if (e == null) {
      if (u === null) return document.createTextNode(p);
      (e = i
        ? document.createElementNS("http://www.w3.org/2000/svg", u)
        : document.createElement(u, p.is && p)),
        (r = null),
        (a = !1);
    }
    if (u === null) y === p || (a && e.data === p) || (e.data = p);
    else {
      if (
        ((r = r && ce.call(e.childNodes)),
        (c = (y = o.props || fe).dangerouslySetInnerHTML),
        (d = p.dangerouslySetInnerHTML),
        !a)
      ) {
        if (r != null)
          for (y = {}, g = 0; g < e.attributes.length; g++)
            y[e.attributes[g].name] = e.attributes[g].value;
        (d || c) &&
          ((d && ((c && d.__html == c.__html) || d.__html === e.innerHTML)) ||
            (e.innerHTML = (d && d.__html) || ""));
      }
      if ((It(e, p, y, i, a), d)) n.__k = [];
      else if (
        (Hn(
          e,
          je((g = n.props.children)) ? g : [g],
          n,
          o,
          t,
          i && u !== "foreignObject",
          r,
          l,
          r ? r[0] : o.__k && Q(o, 0),
          a
        ),
        r != null)
      )
        for (g = r.length; g--; ) r[g] != null && Vn(r[g]);
      a ||
        ("value" in p &&
          (g = p.value) !== void 0 &&
          (g !== e.value ||
            (u === "progress" && !g) ||
            (u === "option" && g !== y.value)) &&
          ge(e, "value", g, y.value, !1),
        "checked" in p &&
          (g = p.checked) !== void 0 &&
          g !== e.checked &&
          ge(e, "checked", g, y.checked, !1));
    }
    return e;
  }
  function Qn(e, n, o) {
    try {
      typeof e == "function" ? e(n) : (e.current = n);
    } catch (t) {
      m.__e(t, o);
    }
  }
  function eo(e, n, o) {
    var t, i;
    if (
      (m.unmount && m.unmount(e),
      (t = e.ref) && ((t.current && t.current !== e.__e) || Qn(t, null, n)),
      (t = e.__c) != null)
    ) {
      if (t.componentWillUnmount)
        try {
          t.componentWillUnmount();
        } catch (r) {
          m.__e(r, n);
        }
      (t.base = t.__P = null), (e.__c = void 0);
    }
    if ((t = e.__k))
      for (i = 0; i < t.length; i++)
        t[i] && eo(t[i], n, o || typeof e.type != "function");
    o || e.__e == null || Vn(e.__e), (e.__ = e.__e = e.__d = void 0);
  }
  function Ft(e, n, o) {
    return this.constructor(e, o);
  }
  function Lt(e, n, o) {
    var t, i, r;
    m.__ && m.__(e, n),
      (i = (t = typeof o == "function") ? null : (o && o.__k) || n.__k),
      (r = []),
      Re(
        n,
        (e = ((!t && o) || n).__k = f(H, null, [e])),
        i || fe,
        fe,
        n.ownerSVGElement !== void 0,
        !t && o ? [o] : i ? null : n.firstChild ? ce.call(n.childNodes) : null,
        r,
        !t && o ? o : i ? i.__e : n.firstChild,
        t
      ),
      Xn(r, e);
  }
  (ce = zn.slice),
    (m = {
      __e: function (e, n, o, t) {
        for (var i, r, l; (n = n.__); )
          if ((i = n.__c) && !i.__)
            try {
              if (
                ((r = i.constructor) &&
                  r.getDerivedStateFromError != null &&
                  (i.setState(r.getDerivedStateFromError(e)), (l = i.__d)),
                i.componentDidCatch != null &&
                  (i.componentDidCatch(e, t || {}), (l = i.__d)),
                l)
              )
                return (i.__E = i);
            } catch (a) {
              e = a;
            }
        throw e;
      },
    }),
    (Dn = 0),
    (ue.prototype.setState = function (e, n) {
      var o;
      (o =
        this.__s != null && this.__s !== this.state
          ? this.__s
          : (this.__s = z({}, this.state))),
        typeof e == "function" && (e = e(z({}, o), this.props)),
        e && z(o, e),
        e != null && this.__v && (n && this._sb.push(n), Kn(this));
    }),
    (ue.prototype.forceUpdate = function (e) {
      this.__v && ((this.__e = !0), e && this.__h.push(e), Kn(this));
    }),
    (ue.prototype.render = H),
    (K = []),
    (Un =
      typeof Promise == "function"
        ? Promise.prototype.then.bind(Promise.resolve())
        : setTimeout),
    (Le = function (e, n) {
      return e.__v.__b - n.__v.__b;
    }),
    (ve.__r = 0);
  var ee,
    x,
    De,
    no,
    ne = 0,
    oo = [],
    _e = [],
    to = m.__b,
    io = m.__r,
    ro = m.diffed,
    so = m.__c,
    ao = m.unmount;
  function Me(e, n) {
    m.__h && m.__h(x, e, ne || n), (ne = 0);
    var o = x.__H || (x.__H = { __: [], __h: [] });
    return e >= o.__.length && o.__.push({ __V: _e }), o.__[e];
  }
  function Y(e) {
    return (ne = 1), jt(fo, e);
  }
  function jt(e, n, o) {
    var t = Me(ee++, 2);
    if (
      ((t.t = e),
      !t.__c &&
        ((t.__ = [
          o ? o(n) : fo(void 0, n),
          function (a) {
            var s = t.__N ? t.__N[0] : t.__[0],
              c = t.t(s, a);
            s !== c && ((t.__N = [c, t.__[1]]), t.__c.setState({}));
          },
        ]),
        (t.__c = x),
        !x.u))
    ) {
      var i = function (a, s, c) {
        if (!t.__c.__H) return !0;
        var d = t.__c.__H.__.filter(function (p) {
          return p.__c;
        });
        if (
          d.every(function (p) {
            return !p.__N;
          })
        )
          return !r || r.call(this, a, s, c);
        var y = !1;
        return (
          d.forEach(function (p) {
            if (p.__N) {
              var u = p.__[0];
              (p.__ = p.__N), (p.__N = void 0), u !== p.__[0] && (y = !0);
            }
          }),
          !(!y && t.__c.props === a) && (!r || r.call(this, a, s, c))
        );
      };
      x.u = !0;
      var r = x.shouldComponentUpdate,
        l = x.componentWillUpdate;
      (x.componentWillUpdate = function (a, s, c) {
        if (this.__e) {
          var d = r;
          (r = void 0), i(a, s, c), (r = d);
        }
        l && l.call(this, a, s, c);
      }),
        (x.shouldComponentUpdate = i);
    }
    return t.__N || t.__;
  }
  function R(e, n) {
    var o = Me(ee++, 3);
    !m.__s && co(o.__H, n) && ((o.__ = e), (o.i = n), x.__H.__h.push(o));
  }
  function Rt(e) {
    return (
      (ne = 5),
      oe(function () {
        return { current: e };
      }, [])
    );
  }
  function oe(e, n) {
    var o = Me(ee++, 7);
    return co(o.__H, n) ? ((o.__V = e()), (o.i = n), (o.__h = e), o.__V) : o.__;
  }
  function P(e, n) {
    return (
      (ne = 8),
      oe(function () {
        return e;
      }, n)
    );
  }
  function Dt() {
    for (var e; (e = oo.shift()); )
      if (e.__P && e.__H)
        try {
          e.__H.__h.forEach(ye), e.__H.__h.forEach(Ue), (e.__H.__h = []);
        } catch (n) {
          (e.__H.__h = []), m.__e(n, e.__v);
        }
  }
  (m.__b = function (e) {
    (x = null), to && to(e);
  }),
    (m.__r = function (e) {
      io && io(e), (ee = 0);
      var n = (x = e.__c).__H;
      n &&
        (De === x
          ? ((n.__h = []),
            (x.__h = []),
            n.__.forEach(function (o) {
              o.__N && (o.__ = o.__N), (o.__V = _e), (o.__N = o.i = void 0);
            }))
          : (n.__h.forEach(ye), n.__h.forEach(Ue), (n.__h = []), (ee = 0))),
        (De = x);
    }),
    (m.diffed = function (e) {
      ro && ro(e);
      var n = e.__c;
      n &&
        n.__H &&
        (n.__H.__h.length &&
          ((oo.push(n) !== 1 && no === m.requestAnimationFrame) ||
            ((no = m.requestAnimationFrame) || Mt)(Dt)),
        n.__H.__.forEach(function (o) {
          o.i && (o.__H = o.i),
            o.__V !== _e && (o.__ = o.__V),
            (o.i = void 0),
            (o.__V = _e);
        })),
        (De = x = null);
    }),
    (m.__c = function (e, n) {
      n.some(function (o) {
        try {
          o.__h.forEach(ye),
            (o.__h = o.__h.filter(function (t) {
              return !t.__ || Ue(t);
            }));
        } catch (t) {
          n.some(function (i) {
            i.__h && (i.__h = []);
          }),
            (n = []),
            m.__e(t, o.__v);
        }
      }),
        so && so(e, n);
    }),
    (m.unmount = function (e) {
      ao && ao(e);
      var n,
        o = e.__c;
      o &&
        o.__H &&
        (o.__H.__.forEach(function (t) {
          try {
            ye(t);
          } catch (i) {
            n = i;
          }
        }),
        (o.__H = void 0),
        n && m.__e(n, o.__v));
    });
  var lo = typeof requestAnimationFrame == "function";
  function Mt(e) {
    var n,
      o = function () {
        clearTimeout(t), lo && cancelAnimationFrame(n), setTimeout(e);
      },
      t = setTimeout(o, 100);
    lo && (n = requestAnimationFrame(o));
  }
  function ye(e) {
    var n = x,
      o = e.__c;
    typeof o == "function" && ((e.__c = void 0), o()), (x = n);
  }
  function Ue(e) {
    var n = x;
    (e.__c = e.__()), (x = n);
  }
  function co(e, n) {
    return (
      !e ||
      e.length !== n.length ||
      n.some(function (o, t) {
        return o !== e[t];
      })
    );
  }
  function fo(e, n) {
    return typeof n == "function" ? n(e) : n;
  }
  const po = ({ onClick: e, ariaLabel: n, hidden: o = !1 }) =>
      f(
        "button",
        {
          type: "button",
          "aria-label": n,
          className: "fides-close-button",
          onClick: e,
          style: { visibility: o ? "hidden" : "visible" },
        },
        f(
          "svg",
          {
            xmlns: "http://www.w3.org/2000/svg",
            width: "16",
            height: "16",
            fill: "none",
          },
          f("path", {
            fill: "#2D3748",
            d: "m8 7.057 3.3-3.3.943.943-3.3 3.3 3.3 3.3-.943.943-3.3-3.3-3.3 3.3-.943-.943 3.3-3.3-3.3-3.3.943-.943 3.3 3.3Z",
          })
        )
      ),
    uo = ({ label: e, status: n }) =>
      f(
        "span",
        { className: "fides-gpc-label" },
        e,
        " ",
        f("span", { className: `fides-gpc-badge fides-gpc-badge-${n}` }, n)
      ),
    Ut = ({ value: e, notice: n }) => {
      const o = U(),
        t = an({ value: e, notice: n, consentContext: o });
      return t === G.NONE
        ? null
        : f(uo, { label: "Global Privacy Control", status: t.valueOf() });
    },
    be = "vendors page.",
    vo = ({
      description: e,
      onVendorPageClick: n,
      allowHTMLDescription: o = !1,
    }) => {
      if (!e) return null;
      if (o)
        return f("div", {
          className: "fides-html-description",
          dangerouslySetInnerHTML: { __html: e },
        });
      if (
        n &&
        (e.endsWith(be) ||
          e.endsWith(`${be}
`))
      ) {
        const t = e.split(be)[0];
        return f(
          "div",
          null,
          t,
          " ",
          f(
            "button",
            { type: "button", className: "fides-link-button", onClick: n },
            be
          )
        );
      }
      return f("div", null, e);
    },
    go = ({
      experience: e,
      onOpen: n,
      onClose: o,
      bannerIsOpen: t,
      children: i,
      onVendorPageClick: r,
      renderButtonGroup: l,
      className: a,
      fidesPreviewMode: s,
    }) => {
      var c, d, y, p;
      const u = Rt(null),
        [g, O] = Y(window.innerWidth < 768);
      R(() => {
        const k = () => {
          O(window.innerWidth < 768);
        };
        return (
          window.addEventListener("resize", k),
          () => {
            window.removeEventListener("resize", k);
          }
        );
      }, []),
        R(() => {
          var k, E;
          const I = (A) => {
              u.current && !u.current.contains(A.target) && o();
            },
            $ = (A) => {
              A.key === "Escape" && o();
            };
          return (
            t &&
            !(
              (E = (k = window.Fides) == null ? void 0 : k.options) != null &&
              E.preventDismissal
            ) &&
            !s
              ? (window.addEventListener("mousedown", I),
                window.addEventListener("keydown", $))
              : (window.removeEventListener("mousedown", I),
                window.removeEventListener("keydown", $)),
            () => {
              window.removeEventListener("mousedown", I),
                window.removeEventListener("keydown", $);
            }
          );
        }, [o, t, u]);
      const b = U().globalPrivacyControl;
      R(() => {
        t && n();
      }, [t, n]);
      const h = e.banner_description || e.description,
        w = e.banner_title || e.title;
      return f(
        "div",
        {
          id: "fides-banner-container",
          className: `fides-banner fides-banner-bottom 
        ${t ? "" : "fides-banner-hidden"} 
        ${a || ""}`,
          ref: u,
        },
        f(
          "div",
          { id: "fides-banner" },
          f(
            "div",
            { id: "fides-banner-inner" },
            f(po, {
              ariaLabel: "Close banner",
              onClick: window.Fides.options.fidesPreviewMode ? () => {} : o,
              hidden:
                (d = (c = window.Fides) == null ? void 0 : c.options) == null
                  ? void 0
                  : d.preventDismissal,
            }),
            f(
              "div",
              {
                id: "fides-banner-inner-container",
                style: { gridTemplateColumns: i ? "1fr 1fr" : "1fr" },
              },
              f(
                "div",
                { id: "fides-banner-inner-description" },
                f(
                  "div",
                  { id: "fides-banner-heading" },
                  f(
                    "div",
                    {
                      id: "fides-banner-title",
                      className: "fides-banner-title",
                    },
                    w
                  ),
                  b &&
                    f(uo, {
                      label: "Global Privacy Control Signal",
                      status: "detected",
                    })
                ),
                f(
                  "div",
                  {
                    id: "fides-banner-description",
                    className: "fides-banner-description",
                  },
                  f(vo, {
                    description: h,
                    onVendorPageClick: r,
                    allowHTMLDescription:
                      (p = (y = window.Fides) == null ? void 0 : y.options) ==
                      null
                        ? void 0
                        : p.allowHTMLDescription,
                  })
                )
              ),
              i,
              !g && l({ isMobile: g })
            ),
            g && l({ isMobile: g })
          )
        )
      );
    };
  function zt(e, n) {
    n === void 0 && (n = {});
    var o = n.insertAt;
    if (!(!e || typeof document > "u")) {
      var t = document.head || document.getElementsByTagName("head")[0],
        i = document.createElement("style");
      (i.type = "text/css"),
        o === "top" && t.firstChild
          ? t.insertBefore(i, t.firstChild)
          : t.appendChild(i),
        i.styleSheet
          ? (i.styleSheet.cssText = e)
          : i.appendChild(document.createTextNode(e));
    }
  }
  var Vt = `:root{--fides-overlay-primary-color:#8243f2;--fides-overlay-background-color:#f7fafc;--fides-overlay-embed-background-color:transparent;--fides-overlay-font-color:#4a5568;--fides-overlay-font-color-dark:#2d3748;--fides-overlay-hover-color:#edf2f7;--fides-overlay-gpc-applied-background-color:#38a169;--fides-overlay-gpc-applied-text-color:#fff;--fides-overlay-gpc-overridden-background-color:#e53e3e;--fides-overlay-gpc-overridden-text-color:#fff;--fides-overlay-background-dark-color:#e2e8f0;--fides-overlay-width:680px;--fides-overlay-primary-button-background-color:var(
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
  zt(Vt);
  var Bt = [
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
    Kt = "Tab",
    Ht = "Escape";
  function S(e) {
    (this._show = this.show.bind(this)),
      (this._hide = this.hide.bind(this)),
      (this._maintainFocus = this._maintainFocus.bind(this)),
      (this._bindKeypress = this._bindKeypress.bind(this)),
      (this.$el = e),
      (this.shown = !1),
      (this._id = this.$el.getAttribute("data-a11y-dialog") || this.$el.id),
      (this._previouslyFocused = null),
      (this._listeners = {}),
      this.create();
  }
  (S.prototype.create = function () {
    this.$el.setAttribute("aria-hidden", !0),
      this.$el.setAttribute("aria-modal", !0),
      this.$el.setAttribute("tabindex", -1),
      this.$el.hasAttribute("role") || this.$el.setAttribute("role", "dialog"),
      (this._openers = te('[data-a11y-dialog-show="' + this._id + '"]')),
      this._openers.forEach(
        function (n) {
          n.addEventListener("click", this._show);
        }.bind(this)
      );
    const e = this.$el;
    return (
      (this._closers = te("[data-a11y-dialog-hide]", this.$el)
        .filter(function (n) {
          return n.closest('[aria-modal="true"], [data-a11y-dialog]') === e;
        })
        .concat(te('[data-a11y-dialog-hide="' + this._id + '"]'))),
      this._closers.forEach(
        function (n) {
          n.addEventListener("click", this._hide);
        }.bind(this)
      ),
      this._fire("create"),
      this
    );
  }),
    (S.prototype.show = function (e) {
      return this.shown
        ? this
        : ((this._previouslyFocused = document.activeElement),
          this.$el.removeAttribute("aria-hidden"),
          (this.shown = !0),
          _o(this.$el),
          document.body.addEventListener("focus", this._maintainFocus, !0),
          document.addEventListener("keydown", this._bindKeypress),
          this._fire("show", e),
          this);
    }),
    (S.prototype.hide = function (e) {
      return this.shown
        ? ((this.shown = !1),
          this.$el.setAttribute("aria-hidden", "true"),
          this._previouslyFocused &&
            this._previouslyFocused.focus &&
            this._previouslyFocused.focus(),
          document.body.removeEventListener("focus", this._maintainFocus, !0),
          document.removeEventListener("keydown", this._bindKeypress),
          this._fire("hide", e),
          this)
        : this;
    }),
    (S.prototype.destroy = function () {
      return (
        this.hide(),
        this._openers.forEach(
          function (e) {
            e.removeEventListener("click", this._show);
          }.bind(this)
        ),
        this._closers.forEach(
          function (e) {
            e.removeEventListener("click", this._hide);
          }.bind(this)
        ),
        this._fire("destroy"),
        (this._listeners = {}),
        this
      );
    }),
    (S.prototype.on = function (e, n) {
      return (
        typeof this._listeners[e] > "u" && (this._listeners[e] = []),
        this._listeners[e].push(n),
        this
      );
    }),
    (S.prototype.off = function (e, n) {
      var o = (this._listeners[e] || []).indexOf(n);
      return o > -1 && this._listeners[e].splice(o, 1), this;
    }),
    (S.prototype._fire = function (e, n) {
      var o = this._listeners[e] || [],
        t = new CustomEvent(e, { detail: n });
      this.$el.dispatchEvent(t),
        o.forEach(
          function (i) {
            i(this.$el, n);
          }.bind(this)
        );
    }),
    (S.prototype._bindKeypress = function (e) {
      const n = document.activeElement;
      (n && n.closest('[aria-modal="true"]') !== this.$el) ||
        (this.shown &&
          e.key === Ht &&
          this.$el.getAttribute("role") !== "alertdialog" &&
          (e.preventDefault(), this.hide(e)),
        this.shown && e.key === Kt && qt(this.$el, e));
    }),
    (S.prototype._maintainFocus = function (e) {
      this.shown &&
        !e.target.closest('[aria-modal="true"]') &&
        !e.target.closest("[data-a11y-dialog-ignore-focus-trap]") &&
        _o(this.$el);
    });
  function Yt(e) {
    return Array.prototype.slice.call(e);
  }
  function te(e, n) {
    return Yt((n || document).querySelectorAll(e));
  }
  function _o(e) {
    var n = e.querySelector("[autofocus]") || e;
    n.focus();
  }
  function Gt(e) {
    return te(Bt.join(","), e).filter(function (n) {
      return !!(n.offsetWidth || n.offsetHeight || n.getClientRects().length);
    });
  }
  function qt(e, n) {
    var o = Gt(e),
      t = o.indexOf(document.activeElement);
    n.shiftKey && t === 0
      ? (o[o.length - 1].focus(), n.preventDefault())
      : !n.shiftKey && t === o.length - 1 && (o[0].focus(), n.preventDefault());
  }
  function ze() {
    te("[data-a11y-dialog]").forEach(function (e) {
      new S(e);
    });
  }
  typeof document < "u" &&
    (document.readyState === "loading"
      ? document.addEventListener("DOMContentLoaded", ze)
      : window.requestAnimationFrame
      ? window.requestAnimationFrame(ze)
      : window.setTimeout(ze, 16));
  const Wt = (e) => {
      const [n, o] = Y(null),
        t = P((i) => {
          if (i !== null) {
            const r = new S(i);
            r
              .on("show", () => {
                document.documentElement.style.overflowY = "hidden";
              })
              .on("hide", (l, a) => {
                (document.documentElement.style.overflowY = ""),
                  e && a instanceof KeyboardEvent && a.key === "Escape" && e();
              }),
              o(r);
          }
        }, []);
      return { instance: n, container: t };
    },
    Jt = ({ role: e, id: n, onClose: o, onEsc: t }) => {
      const { instance: i, container: r } = Wt(t),
        l = e === "alertdialog",
        a = `${n}-title`,
        s = P(() => {
          i && i.hide(), o && o();
        }, [i]);
      return (
        R(
          () => () => {
            i && i.destroy();
          },
          [i]
        ),
        {
          instance: i,
          attributes: {
            container: {
              id: n,
              ref: r,
              role: e,
              tabIndex: -1,
              "aria-modal": !0,
              "aria-hidden": !0,
              "aria-labelledby": a,
            },
            overlay: { onClick: l ? void 0 : s },
            dialog: { role: "document" },
            closeButton: { type: "button", onClick: s },
            title: { role: "heading", "aria-level": 1, id: a },
          },
        }
      );
    },
    Zt = () =>
      f(
        "svg",
        {
          xmlns: "http://www.w3.org/2000/svg",
          width: "18",
          height: "18",
          fill: "currentColor",
        },
        f("path", {
          d: "M9 12.05a.68.68 0 0 0-.68.7c0 .39.32.7.68.7.39 0 .68-.31.68-.7a.66.66 0 0 0-.68-.7Zm0-1.18c.26 0 .44-.2.44-.46V6.19c0-.26-.2-.47-.44-.47a.49.49 0 0 0-.47.47v4.22c0 .25.21.46.47.46Zm7.27 2.27-5.85-9.9c-.3-.5-.83-.8-1.42-.8-.6 0-1.12.3-1.42.8l-5.86 9.9c-.3.5-.3 1.1-.01 1.6.3.51.83.82 1.43.82h11.72c.6 0 1.13-.3 1.43-.82.29-.5.28-1.1-.02-1.6Zm-.82 1.1c-.1.25-.33.38-.62.38H3.14a.7.7 0 0 1-.61-.35.64.64 0 0 1 0-.65l5.86-9.9A.7.7 0 0 1 9 3.37a.7.7 0 0 1 .61.35l5.86 9.9c.1.2.12.44-.02.63Z",
        })
      ),
    Xt = () =>
      U().globalPrivacyControl
        ? f(
            "div",
            { className: "fides-gpc-banner" },
            f("div", { className: "fides-gpc-warning" }, f(Zt, null)),
            f(
              "div",
              null,
              f(
                "p",
                { className: "fides-gpc-header" },
                "Global Privacy Control detected"
              ),
              f(
                "p",
                null,
                "Your global privacy control preference has been honored. You have been automatically opted out of data uses cases which adhere to global privacy control."
              )
            )
          )
        : null;
  var Qt = Object.defineProperty,
    ei = Object.defineProperties,
    ni = Object.getOwnPropertyDescriptors,
    yo = Object.getOwnPropertySymbols,
    oi = Object.prototype.hasOwnProperty,
    ti = Object.prototype.propertyIsEnumerable,
    bo = (e, n, o) =>
      n in e
        ? Qt(e, n, { enumerable: !0, configurable: !0, writable: !0, value: o })
        : (e[n] = o),
    ii = (e, n) => {
      for (var o in n || (n = {})) oi.call(n, o) && bo(e, o, n[o]);
      if (yo) for (var o of yo(n)) ti.call(n, o) && bo(e, o, n[o]);
      return e;
    },
    ri = (e, n) => ei(e, ni(n));
  const mo = ({
    title: e,
    className: n,
    experience: o,
    renderModalFooter: t,
    children: i,
    onVendorPageClick: r,
  }) => {
    var l, a;
    const s = U().globalPrivacyControl;
    return f(
      H,
      null,
      f(
        "div",
        {
          "data-testid": "consent-content",
          id: "fides-consent-content",
          className: n,
        },
        f(
          "div",
          { className: "fides-modal-body" },
          f(
            "div",
            ri(ii({ "data-testid": "fides-modal-title" }, e), {
              className: "fides-modal-title",
            }),
            o.title
          ),
          f(
            "p",
            {
              "data-testid": "fides-modal-description",
              className: "fides-modal-description",
            },
            f(vo, {
              onVendorPageClick: r,
              description: o.description,
              allowHTMLDescription:
                (a = (l = window.Fides) == null ? void 0 : l.options) == null
                  ? void 0
                  : a.allowHTMLDescription,
            })
          ),
          s && f(Xt, null),
          i
        )
      ),
      f("div", { className: "fides-modal-footer" }, t())
    );
  };
  var si = Object.defineProperty,
    ai = Object.defineProperties,
    di = Object.getOwnPropertyDescriptors,
    ho = Object.getOwnPropertySymbols,
    li = Object.prototype.hasOwnProperty,
    ci = Object.prototype.propertyIsEnumerable,
    wo = (e, n, o) =>
      n in e
        ? si(e, n, { enumerable: !0, configurable: !0, writable: !0, value: o })
        : (e[n] = o),
    Ve = (e, n) => {
      for (var o in n || (n = {})) li.call(n, o) && wo(e, o, n[o]);
      if (ho) for (var o of ho(n)) ci.call(n, o) && wo(e, o, n[o]);
      return e;
    },
    Be = (e, n) => ai(e, di(n));
  const fi = ({
    attributes: e,
    experience: n,
    renderModalFooter: o,
    renderModalContent: t,
  }) => {
    const { container: i, overlay: r, dialog: l, title: a, closeButton: s } = e;
    return f(
      "div",
      Be(Ve({ "data-testid": "consent-modal" }, i), {
        className: "fides-modal-container",
      }),
      f("div", Be(Ve({}, r), { className: "fides-modal-overlay" })),
      f(
        "div",
        Be(Ve({ "data-testid": "fides-modal-content" }, l), {
          className: "fides-modal-content",
        }),
        f(
          "div",
          { className: "fides-modal-header" },
          f("div", null),
          f(po, {
            ariaLabel: "Close modal",
            onClick: window.Fides.options.fidesPreviewMode
              ? () => {}
              : s.onClick,
            hidden: window.Fides.options.preventDismissal,
          })
        ),
        f(mo, { title: a, experience: n, renderModalFooter: o }, t())
      )
    );
  };
  var pi = (e, n, o) =>
    new Promise((t, i) => {
      var r = (s) => {
          try {
            a(o.next(s));
          } catch (c) {
            i(c);
          }
        },
        l = (s) => {
          try {
            a(o.throw(s));
          } catch (c) {
            i(c);
          }
        },
        a = (s) => (s.done ? t(s.value) : Promise.resolve(s.value).then(r, l));
      a((o = o.apply(e, n)).next());
    });
  const ui = () => {
      const [e, n] = Y(!1);
      return (
        R(() => {
          n(!0);
        }, []),
        e
      );
    },
    vi = ({ id: e }) => {
      const [n, o] = Y(!1),
        t = P(() => o(!1), []),
        i = P(() => o(!0), []),
        r = P(() => {
          n ? t() : i();
        }, [n, i, t]);
      return {
        isOpen: n,
        onOpen: i,
        onClose: t,
        onToggle: r,
        getButtonProps: () => ({
          "aria-expanded": n,
          "aria-controls": e,
          onClick: r,
        }),
        getDisclosureProps: () => ({
          id: e,
          className: n ? "fides-disclosure-visible" : "fides-disclosure-hidden",
        }),
      };
    },
    D = (e) => (e ? e.map((n) => n.id) : []),
    gi = ({
      notices: e,
      options: n,
      userGeography: o,
      privacyExperience: t,
      acknowledgeMode: i,
    }) => {
      const [r, l] = Y(null),
        a = P(
          (s) =>
            pi(void 0, null, function* () {
              if (
                n.fidesPreviewMode ||
                !s.detail.extraDetails ||
                s.detail.extraDetails.servingComponent === Z.BANNER
              )
                return;
              const c = {
                  browser_identity: s.detail.identity,
                  privacy_experience_id: t.id,
                  user_geography: o,
                  acknowledge_mode: i,
                  privacy_notice_history_ids: e.map(
                    (y) => y.privacy_notice_history_id
                  ),
                  tcf_purpose_consents: D(t?.tcf_purpose_consents),
                  tcf_purpose_legitimate_interests: D(
                    t.tcf_purpose_legitimate_interests
                  ),
                  tcf_special_purposes: D(t?.tcf_special_purposes),
                  tcf_vendor_consents: D(t?.tcf_vendor_consents),
                  tcf_vendor_legitimate_interests: D(
                    t.tcf_vendor_legitimate_interests
                  ),
                  tcf_features: D(t?.tcf_features),
                  tcf_special_features: D(t?.tcf_special_features),
                  tcf_system_consents: D(t?.tcf_system_consents),
                  tcf_system_legitimate_interests: D(
                    t?.tcf_system_legitimate_interests
                  ),
                  serving_component: s.detail.extraDetails.servingComponent,
                },
                d = yield Sn({ request: c, options: n });
              d && l(d);
            }),
          [e, n, i, t, o]
        );
      return (
        R(
          () => (
            window.addEventListener("FidesUIShown", a),
            () => {
              window.removeEventListener("FidesUIShown", a);
            }
          ),
          [a]
        ),
        { servedNotice: r }
      );
    },
    _i = ({
      experience: e,
      options: n,
      cookie: o,
      onOpen: t,
      onDismiss: i,
      renderBanner: r,
      renderModalContent: l,
      renderModalFooter: a,
      onVendorPageClick: s,
    }) => {
      var c;
      const d = ui(),
        [y, p] = Y(!1),
        u = P(
          ({ saved: E = !1 }) => {
            M("FidesModalClosed", o, n.debug, { saved: E }), E || i();
          },
          [o, i, n.debug]
        ),
        { instance: g, attributes: O } = Jt({
          id: "fides-modal",
          role: window.Fides.options.preventDismissal
            ? "alertdialog"
            : "dialog",
          title: ((c = e?.experience_config) == null ? void 0 : c.title) || "",
          onClose: () => {
            u({ saved: !1 });
          },
          onEsc: () => {
            u({ saved: !1 });
          },
        }),
        b = P(() => {
          g && (g.show(), t());
        }, [g, t]),
        h = P(() => {
          g && !n.fidesEmbed && (g.hide(), u({ saved: !0 }));
        }, [g, u, n.fidesEmbed]);
      R(() => {
        n.fidesEmbed && t();
      }, [n, t]),
        R(() => {
          const E = setTimeout(() => {
            p(!0);
          }, 100);
          return () => clearTimeout(E);
        }, [p]),
        R(() => {
          const E = setTimeout(() => {
            const I = n.modalLinkId || "fides-modal-link",
              $ = document.getElementById(I);
            if ($) {
              v(
                n.debug,
                "Modal link element found, updating it to show and trigger modal on click."
              );
              const A = $;
              (A.onclick = () => {
                p(!1), b();
              }),
                A.classList.add("fides-modal-link-shown");
            } else v(n.debug, "Modal link element not found.");
          }, 200);
          return () => clearTimeout(E);
        }, [n.modalLinkId, n.debug, b]);
      const w = oe(
          () =>
            !n.fidesDisableBanner && e.show_banner && rn(e, o) && !n.fidesEmbed,
          [o, e, n]
        ),
        k = () => {
          b(), p(!1);
        };
      return d
        ? e.experience_config
          ? f(
              "div",
              null,
              w &&
                y &&
                window.Fides.options.preventDismissal &&
                f("div", { className: "fides-modal-overlay" }),
              w
                ? r({
                    isOpen: y,
                    onClose: () => {
                      p(!1);
                    },
                    onSave: () => {
                      p(!1);
                    },
                    onManagePreferencesClick: k,
                  })
                : null,
              n.fidesEmbed
                ? f(
                    mo,
                    {
                      title: O.title,
                      className: "fides-embed",
                      experience: e.experience_config,
                      renderModalFooter: () => a({ onClose: h, isMobile: !1 }),
                    },
                    l()
                  )
                : f(fi, {
                    attributes: O,
                    experience: e.experience_config,
                    onVendorPageClick: s,
                    renderModalFooter: () => a({ onClose: h, isMobile: !1 }),
                    renderModalContent: l,
                  })
            )
          : (v(n.debug, "No experience config found"), null)
        : null;
    },
    ie = ({ buttonType: e, label: n, onClick: o, className: t = "" }) =>
      f(
        "button",
        {
          type: "button",
          id: `fides-banner-button-${e.valueOf()}`,
          className: `fides-banner-button fides-banner-button-${e.valueOf()} ${t}`,
          onClick: o,
          "data-testid": `${n}-btn`,
        },
        n || ""
      ),
    xo = ({ experience: e }) =>
      !(e != null && e.privacy_policy_link_label) ||
      !(e != null && e.privacy_policy_url)
        ? null
        : f(
            "div",
            {
              id: "fides-privacy-policy-link",
              style: {
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              },
            },
            f(
              "a",
              {
                href: e.privacy_policy_url,
                rel: "noopener noreferrer",
                target: "_blank",
                className: "fides-privacy-policy",
              },
              e.privacy_policy_link_label
            )
          ),
    yi = ({
      experienceConfig: e,
      onManagePreferencesClick: n,
      firstButton: o,
      onAcceptAll: t,
      onRejectAll: i,
      isMobile: r,
      includePrivacyPolicy: l,
      saveOnly: a = !1,
    }) =>
      f(
        "div",
        { id: "fides-button-group" },
        n
          ? f(
              "div",
              { style: { display: "flex" } },
              f(ie, {
                buttonType: r ? j.SECONDARY : j.TERTIARY,
                label: e.privacy_preferences_link_label,
                onClick: n,
                className: "fides-manage-preferences-button",
              })
            )
          : null,
        l ? f(xo, { experience: e }) : null,
        f(
          "div",
          {
            className: o
              ? "fides-modal-button-group"
              : "fides-banner-button-group",
          },
          o || null,
          !a &&
            f(
              H,
              null,
              f(ie, {
                buttonType: j.PRIMARY,
                label: e.reject_button_label,
                onClick: i,
                className: "fides-reject-all-button",
              }),
              f(ie, {
                buttonType: j.PRIMARY,
                label: e.accept_button_label,
                onClick: t,
                className: "fides-accept-all-button",
              })
            )
        )
      ),
    ko = ({
      experience: e,
      onSave: n,
      onManagePreferencesClick: o,
      enabledKeys: t,
      isInModal: i,
      isAcknowledge: r,
      isMobile: l,
      saveOnly: a = !1,
      fidesPreviewMode: s = !1,
    }) => {
      if (!e.experience_config || !e.privacy_notices) return null;
      const { experience_config: c, privacy_notices: d } = e,
        y = () => {
          s ||
            n(
              B.ACCEPT,
              d.map((g) => g.notice_key)
            );
        },
        p = () => {
          s ||
            n(
              B.REJECT,
              d
                .filter((g) => g.consent_mechanism === F.NOTICE_ONLY)
                .map((g) => g.notice_key)
            );
        },
        u = () => {
          s || n(B.SAVE, t);
        };
      return r
        ? f(
            "div",
            {
              className: `fides-acknowledge-button-container ${
                i ? "" : "fides-banner-acknowledge"
              }`,
            },
            f(ie, {
              buttonType: j.PRIMARY,
              label: c.acknowledge_button_label,
              onClick: y,
              className: "fides-acknowledge-button",
            })
          )
        : f(yi, {
            experienceConfig: c,
            onManagePreferencesClick: o,
            onAcceptAll: y,
            onRejectAll: p,
            firstButton: i
              ? f(ie, {
                  buttonType: a ? j.PRIMARY : j.SECONDARY,
                  label: c.save_button_label,
                  onClick: u,
                  className: "fides-save-button",
                })
              : void 0,
            isMobile: l,
            includePrivacyPolicy: !i,
            saveOnly: a,
          });
    },
    bi = () => f("hr", { className: "fides-divider" }),
    mi = ({ name: e, id: n, checked: o, onChange: t, disabled: i }) => {
      const r = `toggle-${n}`;
      return f(
        "label",
        {
          className: "fides-toggle",
          htmlFor: e,
          "data-testid": `toggle-${e}`,
          id: r,
        },
        f("input", {
          type: "checkbox",
          name: e,
          className: "fides-toggle-input",
          onChange: () => {
            t(n);
          },
          checked: o,
          role: "switch",
          "aria-labelledby": r,
          disabled: i,
        }),
        f(
          "span",
          { className: "fides-toggle-display", hidden: !0 },
          o ? "On" : "Off"
        )
      );
    };
  var hi = Object.defineProperty,
    wi = Object.defineProperties,
    xi = Object.getOwnPropertyDescriptors,
    Co = Object.getOwnPropertySymbols,
    ki = Object.prototype.hasOwnProperty,
    Ci = Object.prototype.propertyIsEnumerable,
    Eo = (e, n, o) =>
      n in e
        ? hi(e, n, { enumerable: !0, configurable: !0, writable: !0, value: o })
        : (e[n] = o),
    Oo = (e, n) => {
      for (var o in n || (n = {})) ki.call(n, o) && Eo(e, o, n[o]);
      if (Co) for (var o of Co(n)) Ci.call(n, o) && Eo(e, o, n[o]);
      return e;
    },
    Ei = (e, n) => wi(e, xi(n));
  const Oi = ({
      dataUse: e,
      checked: n,
      onToggle: o,
      children: t,
      badge: i,
      gpcBadge: r,
      disabled: l,
      isHeader: a,
      includeToggle: s = !0,
    }) => {
      const {
          isOpen: c,
          getButtonProps: d,
          getDisclosureProps: y,
          onToggle: p,
        } = vi({ id: e.key }),
        u = (b) => {
          (b.code === "Space" || b.code === "Enter") && p();
        },
        g = t != null,
        O = g ? d() : {};
      return f(
        "div",
        {
          className:
            c && g
              ? "fides-notice-toggle fides-notice-toggle-expanded"
              : "fides-notice-toggle",
        },
        f(
          "div",
          { key: e.key, className: "fides-notice-toggle-title" },
          f(
            "span",
            Ei(
              Oo({ role: "button", tabIndex: 0, onKeyDown: g ? u : void 0 }, O),
              {
                className: a
                  ? "fides-notice-toggle-trigger fides-notice-toggle-header"
                  : "fides-notice-toggle-trigger",
              }
            ),
            f(
              "span",
              { className: "fides-flex-center fides-justify-space-between" },
              e.name,
              i ? f("span", { className: "fides-notice-badge" }, i) : null
            ),
            r
          ),
          s
            ? f(mi, {
                name: e.name || "",
                id: e.key,
                checked: n,
                onChange: o,
                disabled: l,
              })
            : null
        ),
        t ? f("div", Oo({}, y()), t) : null
      );
    },
    Pi = ({ notices: e, enabledNoticeKeys: n, onChange: o }) => {
      const t = (i) => {
        n.indexOf(i) === -1 ? o([...n, i]) : o(n.filter((r) => r !== i));
      };
      return f(
        "div",
        null,
        e.map((i, r) => {
          const l = n.indexOf(i.notice_key) !== -1,
            a = r === e.length - 1,
            s = { key: i.notice_key, name: i.name };
          return f(
            "div",
            null,
            f(
              Oi,
              {
                dataUse: s,
                checked: l,
                onToggle: t,
                gpcBadge: f(Ut, { notice: i, value: l }),
                disabled: i.consent_mechanism === F.NOTICE_ONLY,
              },
              i.description
            ),
            a ? null : f(bi, null)
          );
        })
      );
    },
    $i = ({ experience: e, options: n, fidesRegionString: o, cookie: t }) => {
      const i = oe(
          () =>
            e.privacy_notices
              ? e.privacy_notices.map((b) =>
                  Oe(b, U(), t) ? b.notice_key : ""
                )
              : [],
          [t, e]
        ),
        [r, l] = Y(i),
        a = oe(() => {
          var b;
          return (b = e.privacy_notices) != null ? b : [];
        }, [e.privacy_notices]),
        s = a.every((b) => b.consent_mechanism === F.NOTICE_ONLY),
        { servedNotice: c } = gi({
          notices: a,
          options: n,
          userGeography: o,
          acknowledgeMode: s,
          privacyExperience: e,
        }),
        d = (b, h) =>
          b.map((w) => {
            const k = X(h.includes(w.notice_key), w.consent_mechanism);
            return new se(w, k);
          }),
        y = P(
          (b, h) => {
            const w = d(a, h);
            Ln({
              consentPreferencesToSave: w,
              experience: e,
              consentMethod: b,
              options: n,
              userLocationString: o,
              cookie: t,
              servedNoticeHistoryId: c?.served_notice_history_id,
              updateCookie: (k) => Ie(k, w),
            }),
              l(h);
          },
          [a, t, o, e, n, c]
        ),
        p = P(() => {
          M("FidesUIShown", t, n.debug, { servingComponent: Z.BANNER });
        }, [t, n.debug]),
        u = P(() => {
          M("FidesUIShown", t, n.debug, { servingComponent: Z.OVERLAY });
        }, [t, n.debug]),
        g = P(() => {
          y(B.DISMISS, i);
        }, [y, i]);
      if (!e.experience_config)
        return v(n.debug, "No experience config found"), null;
      const O = e.experience_config;
      return f(_i, {
        options: n,
        experience: e,
        cookie: t,
        onOpen: u,
        onDismiss: g,
        renderBanner: ({
          isOpen: b,
          onClose: h,
          onSave: w,
          onManagePreferencesClick: k,
        }) =>
          f(go, {
            bannerIsOpen: b,
            fidesPreviewMode: n.fidesPreviewMode,
            onOpen: p,
            onClose: () => {
              h(), g();
            },
            experience: O,
            renderButtonGroup: ({ isMobile: E }) =>
              f(ko, {
                experience: e,
                onManagePreferencesClick: k,
                enabledKeys: r,
                onSave: (I, $) => {
                  y(I, $), w();
                },
                isAcknowledge: s,
                isMobile: E,
                fidesPreviewMode: n.fidesPreviewMode,
              }),
          }),
        renderModalContent: () =>
          f(
            "div",
            null,
            f(
              "div",
              { className: "fides-modal-notices" },
              f(Pi, {
                notices: a,
                enabledNoticeKeys: r,
                onChange: (b) => {
                  n.fidesPreviewMode || (l(b), M("FidesUIChanged", t, n.debug));
                },
              })
            )
          ),
        renderModalFooter: ({ onClose: b, isMobile: h }) =>
          f(
            H,
            null,
            f(ko, {
              experience: e,
              enabledKeys: r,
              onSave: (w, k) => {
                y(w, k), b();
              },
              isInModal: !0,
              isAcknowledge: s,
              isMobile: h,
              saveOnly: a.length === 1,
              fidesPreviewMode: n.fidesPreviewMode,
            }),
            f(xo, { experience: e.experience_config })
          ),
      });
    };
  var Ni = Object.defineProperty,
    Po = Object.getOwnPropertySymbols,
    Si = Object.prototype.hasOwnProperty,
    Ti = Object.prototype.propertyIsEnumerable,
    $o = (e, n, o) =>
      n in e
        ? Ni(e, n, { enumerable: !0, configurable: !0, writable: !0, value: o })
        : (e[n] = o),
    Ii = (e, n) => {
      for (var o in n || (n = {})) Si.call(n, o) && $o(e, o, n[o]);
      if (Po) for (var o of Po(n)) Ti.call(n, o) && $o(e, o, n[o]);
      return e;
    };
  const Ai = (e, n) => {
    Lt(f($i, Ii({}, e)), n);
  };
  var Fi = (e, n, o) =>
    new Promise((t, i) => {
      var r = (s) => {
          try {
            a(o.next(s));
          } catch (c) {
            i(c);
          }
        },
        l = (s) => {
          try {
            a(o.throw(s));
          } catch (c) {
            i(c);
          }
        },
        a = (s) => (s.done ? t(s.value) : Promise.resolve(s.value).then(r, l));
      a((o = o.apply(e, n)).next());
    });
  function Li(e) {
    return Fi(this, null, function* () {
      var n;
      if (!((n = e.options.apiOptions) != null && n.getPreferencesFn))
        return null;
      v(e.options.debug, "Calling custom get preferences fn");
      try {
        return yield e.options.apiOptions.getPreferencesFn(e);
      } catch (o) {
        return (
          v(
            e.options.debug,
            "Error retrieving preferences from custom API, continuing. Error: ",
            o
          ),
          null
        );
      }
    });
  }
  var ji = Object.defineProperty,
    Ri = Object.defineProperties,
    Di = Object.getOwnPropertyDescriptors,
    No = Object.getOwnPropertySymbols,
    Mi = Object.prototype.hasOwnProperty,
    Ui = Object.prototype.propertyIsEnumerable,
    So = (e, n, o) =>
      n in e
        ? ji(e, n, { enumerable: !0, configurable: !0, writable: !0, value: o })
        : (e[n] = o),
    J = (e, n) => {
      for (var o in n || (n = {})) Mi.call(n, o) && So(e, o, n[o]);
      if (No) for (var o of No(n)) Ui.call(n, o) && So(e, o, n[o]);
      return e;
    },
    To = (e, n) => Ri(e, Di(n)),
    Io = (e, n, o) =>
      new Promise((t, i) => {
        var r = (s) => {
            try {
              a(o.next(s));
            } catch (c) {
              i(c);
            }
          },
          l = (s) => {
            try {
              a(o.throw(s));
            } catch (c) {
              i(c);
            }
          },
          a = (s) =>
            s.done ? t(s.value) : Promise.resolve(s.value).then(r, l);
        a((o = o.apply(e, n)).next());
      });
  let me;
  const zi = (e, n, o, t) =>
    Io(void 0, null, function* () {
      let i = n;
      const r = pn(e.consent);
      return t && r && (i = Te({ experience: n, cookie: e, debug: o })), i;
    });
  (me = {
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
    gtm: Ao,
    init: (e) =>
      Io(void 0, null, function* () {
        var n, o;
        const t = Pt(e),
          i = yield Li(e),
          r = { optionsOverrides: t, consentPrefsOverrides: i };
        e.options = J(J({}, e.options), r.optionsOverrides);
        const l = J(
            J({}, $t(e)),
            (n = r.consentPrefsOverrides) == null ? void 0 : n.consent
          ),
          a = Nt(
            To(J({}, e), { cookie: l, updateExperienceFromCookieConsent: Te })
          );
        a && (Object.assign(me, a), M("FidesInitialized", l, e.options.debug));
        const s = (o = a?.experience) != null ? o : e.experience,
          c = yield St(
            To(J({}, e), {
              cookie: l,
              experience: s,
              renderOverlay: Ai,
              updateExperience: ({
                cookie: d,
                experience: y,
                debug: p,
                isExperienceClientSideFetched: u,
              }) => zi(d, y, p, u),
            })
          );
        Object.assign(me, c), M("FidesInitialized", l, e.options.debug);
      }),
    initialized: !1,
    meta: Lo,
    shopify: jo,
  }),
    typeof window < "u" && (window.Fides = me),
    (_.BannerEnabled = Qe),
    (_.ButtonType = j),
    (_.CONSENT_COOKIE_MAX_AGE_DAYS = cn),
    (_.CONSENT_COOKIE_NAME = Ne),
    (_.ComponentType = L),
    (_.ConsentBanner = go),
    (_.ConsentMechanism = F),
    (_.ConsentMethod = B),
    (_.EnforcementLevel = Xe),
    (_.FidesEndpointPaths = On),
    (_.GpcStatus = G),
    (_.RequestOrigin = en),
    (_.SaveConsentPreference = se),
    (_.ServingComponent = Z),
    (_.UserConsentPreference = T),
    (_.consentCookieObjHasSomeConsentSet = pn),
    (_.constructFidesRegionString = Pe),
    (_.debugLog = v),
    (_.dispatchFidesEvent = M),
    (_.experienceIsValid = tn),
    (_.fetchExperience = Pn),
    (_.generateFidesUserDeviceId = un),
    (_.getConsentContext = U),
    (_.getCookieByName = Se),
    (_.getGeolocation = Tn),
    (_.getGpcStatusFromNotice = an),
    (_.getOrMakeFidesCookie = _n),
    (_.getTcfDefaultPreference = Ho),
    (_.getWindowObjFromPath = sn),
    (_.initOverlay = jn),
    (_.isNewFidesCookie = vn),
    (_.isPrivacyExperience = q),
    (_.makeConsentDefaultsLegacy = bn),
    (_.makeFidesCookie = gn),
    (_.noticeHasConsentInCookie = ae),
    (_.patchNoticesServed = Sn),
    (_.patchUserPreference = Nn),
    (_.removeCookiesFromBrowser = mn),
    (_.resolveConsentValue = Oe),
    (_.resolveLegacyConsentValue = nn),
    (_.saveFidesCookie = yn),
    (_.shouldResurfaceConsent = rn),
    (_.transformConsentToFidesUserPreference = X),
    (_.transformTcfPreferencesToCookieKeys = nt),
    (_.transformUserPreferenceToBoolean = de),
    (_.updateCookieFromNoticePreferences = Ie),
    (_.updateExperienceFromCookieConsentNotices = Te),
    (_.validateOptions = on);
});
