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
        .to.match(/^\s+\(function/, "should be an IIFE")
        .to.match(/\}\)\(\);\s+$/, "should be an IIFE");
      expect(response.body)
        .to.match(/var fidesConfig = \{/, "should bundle Fides.init")
        .to.match(/Fides.init\(fidesConfig\);/, "should bundle Fides.init");
      const matches = response.body.match(
        /var fidesConfig = (?<json>\{.*?\});/
      );
      expect(matches).to.have.nested.property("groups.json");
      expect(JSON.parse(matches.groups.json))
        .to.have.nested.property("consent.options")
        .to.have.length(3);
    });
  });

  describe("when pre-fetching location", () => {
    it("returns location if provided as a '?location' query param", () => {
      cy.request("/fides.js?location=US-CA").then((response) => {
        expect(response.body).to.match(/var fidesConfig = \{/);
        const matches = response.body.match(
          /var fidesConfig = (?<json>\{.*?\});/
        );
        expect(JSON.parse(matches.groups.json))
          .to.have.nested.property("location")
          .to.deep.equal({
            location: "US-CA",
            country: "US",
            region: "CA",
          });
      });
    });

    it("returns location if provided as CloudFront location headers", () => {
      cy.request({
        url: "/fides.js",
        headers: {
          "CloudFront-Viewer-Country": "FR",
          "CloudFront-Viewer-Country-Region": "IDF",
        }
      }).then((response) => {
        expect(response.body).to.match(/var fidesConfig = \{/);
        const matches = response.body.match(
          /var fidesConfig = (?<json>\{.*?\});/
        );
        expect(JSON.parse(matches.groups.json))
          .to.have.nested.property("location")
          .to.deep.equal({
            location: "FR-IDF",
            country: "FR",
            region: "IDF",
          });
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

    it("stores publicly for at least one hour, at most one day", () => {
      cy.get("@cacheHeaders").should("match", /public/);
      cy.get("@cacheHeaders")
        .invoke("match", /max-age=(?<expiry>\d+)/)
        .its("groups.expiry")
        .then(parseInt)
        .should("be.within", 3600, 86400);
    });

    it("generates 'etag' that is consistent when re-requested", () => {
      cy.request("/fides.js")
        .should("have.nested.property", "headers.etag")
        .then((etag) => {
          cy.get("@etag").should("eq", etag);
        });
    });

    it("generates 'etag' that varies based on location query params", () => {
      cy.request("/fides.js?location=US-CA")
        .should("have.nested.property", "headers.etag")
        .as("USCATag")
        .then((etag) => {
          cy.get("@etag").should("not.eq", etag);
        });

      // Fetch a second time with a different location param
      cy.request("/fides.js?location=FR")
        .should("have.nested.property", "headers.etag")
        .then((etag) => {
          cy.get("@etag").should("not.eq", etag);
          cy.get("@USCATag").should("not.eq", etag);
        });
    });

    it("generates 'etag' that varies based on Cloudfront location headers", () => {
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

      // Fetch a second time with different location headers
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

    it("returns 'vary' header for supported Cloudfront location headers", () => {
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
});
