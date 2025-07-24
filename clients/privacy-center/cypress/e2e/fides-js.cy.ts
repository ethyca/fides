import { DEFAULT_FIDES_JS_MAX_AGE_SECONDS } from "~/app/server-utils/loadEnvironmentVariables";

describe("fides.js API route", () => {
  it("returns the fides.js package bundled with the global config", () => {
    cy.request("/fides.js").then((response) => {
      expect(response.status).to.eq(200);
      expect(response)
        .to.have.property("headers")
        .to.have.property("content-type")
        .to.eql("application/javascript");

      // Run a few checks on the "bundled" response body, which should:
      // 1) Be an IIFE that...
      // 2) ...includes a call to Fides.init with a config JSON that...
      // 3) ...is populated with the config.json options
      expect(response.body)
        .to.match(/^\(function/, "should be an IIFE")
        .to.match(/\}\)\(\);\s+$/, "should be an IIFE");
      expect(response.body)
        .to.match(/window.Fides.config = \{/, "should bundle Fides.init")
        .to.match(/Fides.init\(\);/, "should call Fides.init");
      const matches = response.body.match(
        /window.Fides.config = (?<json>\{.*?\});/,
      );
      expect(matches).to.have.nested.property("groups.json");
      expect(JSON.parse(matches.groups.json))
        .to.have.nested.property("consent.options")
        .to.have.length(3);
    });
  });

  it("supports /fides-consent.js route for backwards-compatibility", () => {
    cy.request("/fides-consent.js").then((legacyResponse) => {
      expect(legacyResponse.status).to.eq(200);
      expect(legacyResponse)
        .to.have.property("headers")
        .to.have.property("content-type")
        .to.eql("application/javascript");

      cy.request("/fides.js").then((standardResponse) => {
        expect(standardResponse.body).equals(legacyResponse.body);
      });
    });
  });

  describe("when pre-fetching geolocation", () => {
    it("returns geolocation if provided as a '?geolocation' query param", () => {
      cy.request("/fides.js?geolocation=US-CA").then((response) => {
        expect(response.body).to.match(/window.Fides.config = \{/);
        const matches = response.body.match(
          /window.Fides.config = (?<json>\{.*?\});/,
        );
        expect(JSON.parse(matches.groups.json))
          .to.have.nested.property("geolocation")
          .to.deep.equal({
            location: "US-CA",
            country: "US",
            region: "CA",
          });
      });
    });

    it("returns geolocation if provided as CloudFront geolocation headers", () => {
      cy.request({
        url: "/fides.js",
        headers: {
          "CloudFront-Viewer-Country": "FR",
          "CloudFront-Viewer-Country-Region": "IDF",
        },
      }).then((response) => {
        expect(response.body).to.match(/window.Fides.config = \{/);
        const matches = response.body.match(
          /window.Fides.config = (?<json>\{.*?\});/,
        );
        expect(JSON.parse(matches.groups.json))
          .to.have.nested.property("geolocation")
          .to.deep.equal({
            location: "FR-IDF",
            country: "FR",
            region: "IDF",
          });
      });
    });
  });

  describe("when GPP is forced as a '?gpp' query param", () => {
    it("always returns GPP extension regardless of location", () => {
      cy.request("/fides.js?gpp=true").then((response) => {
        expect(response.body).to.match(/window.__gpp/);
      });
      cy.request("/fides.js?gpp=true&geolocation=US-ID").then((response) => {
        expect(response.body).to.match(/window.__gpp/);
      });
      cy.request("/fides.js?gpp=true&geolocation=US-CA").then((response) => {
        expect(response.body).to.match(/window.__gpp/);
      });
      cy.request("/fides.js?gpp=true&geolocation=FR-IDF").then((response) => {
        expect(response.body).to.match(/window.__gpp/);
      });
      cy.request("/fides.js?geolocation=US-ID").then((response) => {
        expect(response.body).not.to.match(/window.__gpp/);
      });
    });
  });

  it("caches in the browser", () => {
    cy.intercept("/fides.js").as("fidesJS");

    // Load the demo page 3 times, and check /fides.js is called *at most* once
    // NOTE: Depending on browser cache, it might not be called at all - so zero
    // times is a valid number of calls
    cy.visit("/fides-js-demo.html");
    cy.visit("/fides-js-demo.html");
    cy.visit("/fides-js-demo.html");
    cy.get("@fidesJS.all").its("length").should("be.within", 0, 1);
  });

  describe("when generating cache-control headers", () => {
    beforeEach(() => {
      cy.request("/fides.js").then((response) => {
        expect(response.status).to.eq(200);
        cy.wrap(response.headers).as("headers");
        cy.get("@headers").should("have.property", "etag").as("etag");
        cy.get("@headers")
          .should("have.property", "cache-control")
          .as("cacheHeaders");
      });
    });

    it("stores publicly for FIDES_PRIVACY_CENTER__FIDES_JS_MAX_AGE_SECONDS seconds", () => {
      // NOTE: It's not possible to modify the environment variable in the test,
      // so we just check the default value is respected here
      cy.get("@cacheHeaders").should("match", /public/);
      cy.get("@cacheHeaders")
        .invoke("match", /max-age=(?<expiry>\d+)/)
        .its("groups.expiry")
        .then(parseInt)
        .should("equal", DEFAULT_FIDES_JS_MAX_AGE_SECONDS);
    });

    it("generates 'etag' that is consistent when re-requested", () => {
      cy.request("/fides.js")
        .should("have.nested.property", "headers.etag")
        .then((etag) => {
          cy.get("@etag").should("eq", etag);
        });
    });

    it("generates 'etag' that varies based on geolocation query params", () => {
      cy.request("/fides.js?geolocation=US-CA")
        .should("have.nested.property", "headers.etag")
        .as("USCATag")
        .then((etag) => {
          cy.get("@etag").should("not.eq", etag);
        });

      // Fetch a second time with a different geolocation param
      cy.request("/fides.js?geolocation=FR")
        .should("have.nested.property", "headers.etag")
        .then((etag) => {
          cy.get("@etag").should("not.eq", etag);
          cy.get("@USCATag").should("not.eq", etag);
        });
    });

    it("generates 'etag' that varies based on Cloudfront geolocation headers", () => {
      cy.request({
        url: "/fides.js",
        headers: {
          "Cloudfront-Viewer-Country": "US",
          "Cloudfront-Viewer-Country-Region": "CA",
        },
      })
        .should("have.nested.property", "headers.etag")
        .as("USCATag")
        .then((etag) => {
          cy.get("@etag").should("not.eq", etag);
        });

      // Fetch a second time with different geolocation headers
      cy.request({
        url: "/fides.js",
        headers: {
          "Cloudfront-Viewer-Country": "FR",
        },
      })
        .should("have.nested.property", "headers.etag")
        .as("headersTag")
        .then((etag) => {
          cy.get("@etag").should("not.eq", etag);
          cy.get("@USCATag").should("not.eq", etag);
        });
    });

    it("returns 'vary' header for supported Cloudfront geolocation headers", () => {
      const expected = [
        "cloudfront-viewer-country",
        "cloudfront-viewer-country-region",
      ];
      cy.get("@headers")
        .should("have.property", "vary")
        .then((vary: any) => {
          const varyHeaders = (vary as string).replace(" ", "").split(",");
          expect(varyHeaders).to.include.members(expected);
        });
    });
  });

  describe("when disabling initialization", () => {
    it("does not call widnow.Fides.init", () => {
      cy.request("/fides.js?initialize=false").then((response) => {
        expect(response.body).not.to.match(/window.Fides.init(fidesConfig)/);
      });
    });
  });
});

// Convert this to a module instead of script (allows import/export)
export {};
