import {
  CONSENT_COOKIE_NAME,
  ExperienceComponent,
  ExperienceDeliveryMechanism,
  FidesCookie,
} from "fides-js";

describe("Consent banner", () => {

  describe("when overlay is disabled", () => {
    beforeEach(() => {
      // todo- need a better test pattern for overriding default config
      cy.fixture("consent/test_banner_options.json").then((config) => {
        config.options.isOverlayDisabled = true;
        cy.visitConsentDemo(config);
      })
    });

    it("does not render", () => {
      cy.get("div#fides-consent-banner").should("not.exist");
      cy.contains("button", "Accept Test").should("not.exist");
    });
    it.skip("hides the modal link", () => {
      // TODO: add when we have link binding working
      expect(false).is.eql(true);
    })
  });

  describe("when overlay is not disabled", () => {
    describe("happy path", () => {
      beforeEach(() => {
        cy.fixture("consent/test_banner_options.json").then((config) => {
          config.options.isOverlayDisabled = false;
          cy.visitConsentDemo(config);
        })
      });
      it("should render the expected HTML banner", () => {
        cy.get("div#fides-consent-banner.fides-consent-banner").within(() => {
          cy.get(
              "div#fides-consent-banner-description.fides-consent-banner-description"
          ).contains(
              "This test website is overriding the banner description label."
          );
          cy.get(
              "div#fides-consent-banner-buttons.fides-consent-banner-buttons"
          ).within(() => {
            cy.get(
                "button#fides-consent-banner-button-tertiary.fides-consent-banner-button.fides-consent-banner-button-tertiary"
            ).contains("Manage Preferences");
            cy.get(
                "button#fides-consent-banner-button-secondary.fides-consent-banner-button.fides-consent-banner-button-secondary"
            ).contains("Reject Test");
            cy.get(
                "button#fides-consent-banner-button-primary.fides-consent-banner-button.fides-consent-banner-button-primary"
            ).contains("Accept Test");
            // Order matters - it should always be tertiary, then secondary, then primary!
            cy.get("button")
                .eq(0)
                .should("have.id", "fides-consent-banner-button-tertiary");
            cy.get("button")
                .eq(1)
                .should("have.id", "fides-consent-banner-button-secondary");
            cy.get("button")
                .eq(2)
                .should("have.id", "fides-consent-banner-button-primary");
          });
        });
      });
      it.skip("hides the modal link", () => {
        // TODO: add when we have link binding working
        expect(false).is.eql(true);
      })

      it("should allow accepting all", () => {
        cy.contains("button", "Accept Test").should("be.visible").click();
        cy.waitUntilCookieExists(CONSENT_COOKIE_NAME).then(() => {
          cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
            const cookieKeyConsent: FidesCookie = JSON.parse(
                decodeURIComponent(cookie!.value)
            );
            expect(cookieKeyConsent.consent)
                .property("data_sales")
                .is.eql(true);
            expect(cookieKeyConsent.consent).property("tracking").is.eql(true);
          });
          cy.contains("button", "Accept Test").should("not.be.visible");
        });
      });

      it("should support rejecting all consent options", () => {
        cy.contains("button", "Reject Test").should("be.visible").click();
        cy.waitUntilCookieExists(CONSENT_COOKIE_NAME).then(() => {
          cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
            const cookieKeyConsent: FidesCookie = JSON.parse(
                decodeURIComponent(cookie!.value)
            );
            expect(cookieKeyConsent.consent)
                .property("data_sales")
                .is.eql(false);
            expect(cookieKeyConsent.consent).property("tracking").is.eql(false);
          });
        });
      });

      it("should navigate to Privacy Center to manage consent options", () => {
        cy.contains("button", "Manage Preferences")
            .should("be.visible")
            .click();
        cy.url().should("equal", "http://localhost:3000/");
      });

      it.skip("should save the consent request to the Fides API", () => {
        // TODO: add tests for saving to API (ie PATCH /api/v1/consent-request/{id}/preferences...)
        expect(false).is.eql(true);
      });

      it.skip("should support option to display at top or bottom of page", () => {
        // TODO: add tests for top/bottom
        expect(false).is.eql(true);
      });

      it.skip("should support styling with CSS variables", () => {
        // TODO: add tests for CSS
        expect(false).is.eql(true);
      });
    })

    describe("when GPC flag is found, and notices apply to GPC", () => {
      it.skip("sends GPC consent override downstream to Fides API", () => {
        // TODO: add tests for GPC
        expect(false).is.eql(true);
      });

      it.skip("stores consent in cookie", () => {
        // TODO: add tests for GPC
        expect(false).is.eql(true);
      })
    })
    describe("when GPC flag is found, and no notices apply to GPC", () => {
      it.skip("does not send GPC consent override downstream to Fides API", () => {
        // TODO: add tests for GPC
        expect(false).is.eql(true);
      });

      it.skip("does not store consent in cookie", () => {
        // TODO: add tests for GPC
        expect(false).is.eql(true);
      })
    })
    describe("when no GPC flag is found, and notices apply to GPC", () => {
      it.skip("does not send GPC consent override downstream to Fides API", () => {
        // TODO: add tests for GPC
        expect(false).is.eql(true);
      });

      it.skip("does not store consent in cookie", () => {
        // TODO: add tests for GPC
        expect(false).is.eql(true);
      })
    })
    describe("when experience component is not an overlay", () => {
      beforeEach(() => {
        cy.fixture("consent/test_banner_options.json").then((config) => {
          config.experience.component = ExperienceComponent.PRIVACY_CENTER;
          cy.visitConsentDemo(config);
        })
      });

      it("does not render", () => {
        cy.get("div#fides-consent-banner").should("not.exist");
        cy.contains("button", "Accept Test").should("not.exist");
      });
      it.skip("hides the modal link", () => {
        // TODO: add when we have link binding working
        expect(false).is.eql(true);
      })
    })

    describe("when experience is not provided, and valid geolocation is provided", () => {
      beforeEach(() => {
        cy.fixture("consent/test_banner_options.json").then((config) => {
          config.experience = undefined;
          config.geolocation = {
            country: "US",
            location: "US-CA",
            region: "CA"
          }
          cy.visitConsentDemo(config);
        })
      });

      it.skip("renders the banner", () => {
        // TODO: add when we are able to retrieve geolocation via API from fides.js
        expect(false).is.eql(true);
      });
      it.skip("hides the modal link", () => {
        // TODO: add when we have link binding working
        expect(false).is.eql(true);
      })
    })

    describe("when experience is not provided, and geolocation is not provided", () => {
      beforeEach(() => {
        cy.fixture("consent/test_banner_options.json").then((config) => {
          config.experience = undefined;
          config.geolocation = undefined;
          config.options.isGeolocationEnabled = true;
          cy.visitConsentDemo(config);
        })
      });

      it.skip("fetches geolocation from API", () => {
        // TODO: add when we have geolocation API call
        expect(false).is.eql(true);
      })

      describe("when geolocation is successful", function () {
        // TODO: add when we have geolocation and experience API calls
        it.skip("retrieves experience from API", () => {
          expect(false).is.eql(true);
        })
        it.skip("renders the banner", () => {
          expect(false).is.eql(true);
        })
        it.skip("hides the modal link", () => {
          // TODO: add when we have link binding working
          expect(false).is.eql(true);
        })
      });

      describe("when geolocation is not successful", function () {
        // TODO: add when we have geolocation API call
        it.skip("does not render", () => {
          expect(false).is.eql(true);
        })
        it.skip("hides the modal link", () => {
          // TODO: add when we have link binding working
          expect(false).is.eql(true);
        })
      });
    })

    // TODO: it should be possible in the future to filter for experience on just country
    describe("when experience is not provided, and geolocation is invalid", () => {
      beforeEach(() => {
        cy.fixture("consent/test_banner_options.json").then((config) => {
          config.experience = undefined;
          config.geolocation = {
            country: "US",
          }
          config.options.isGeolocationEnabled = true;
          cy.visitConsentDemo(config);
        })
      });

      it.skip("fetches geolocation from API and renders the banner", () => {
        // TODO: add when we have geolocation API call
        expect(false).is.eql(true);
      })

      it.skip("hides the modal link", () => {
        // TODO: add when we have link binding working
        expect(false).is.eql(true);
      })
    })

    describe("when experience is not provided, and geolocation is not provided, but geolocation is disabled", () => {
      beforeEach(() => {
        cy.fixture("consent/test_banner_options.json").then((config) => {
          config.experience = undefined;
          config.geolocation = undefined;
          config.options.isGeolocationEnabled = false;
          cy.visitConsentDemo(config);
        })
      });

      it("does not render", () => {
        cy.get("div#fides-consent-banner").should("not.exist");
        cy.contains("button", "Accept Test").should("not.exist");
      });

      it.skip("hides the modal link", () => {
        // TODO: add when we have link binding working
        expect(false).is.eql(true);
      })
    })

    describe("when experience contains no notices", () => {
      beforeEach(() => {
        cy.fixture("consent/test_banner_options.json").then((config) => {
          config.experience.privacy_notices = [];
          cy.visitConsentDemo(config);
        })
      });

      it("does not render", () => {
        cy.get("div#fides-consent-banner").should("not.exist");
        cy.contains("button", "Accept Test").should("not.exist");
      });

      it.skip("hides the modal link", () => {
        // TODO: add when we have link binding working
        expect(false).is.eql(true);
      })
    })

    describe("when experience delivery mechanism is link", () => {
      beforeEach(() => {
        cy.fixture("consent/test_banner_options.json").then((config) => {
          config.experience.delivery_mechanism = ExperienceDeliveryMechanism.LINK;
          cy.visitConsentDemo(config);
        })
      });

      it("does not render banner", () => {
        cy.get("div#fides-consent-banner").should("not.exist");
        cy.contains("button", "Accept Test").should("not.exist");
      });

      it.skip("shows the modal link", () => {
        // TODO: add when we have link binding working
        expect(false).is.eql(true);
      })

      describe("modal link click", () => {
        it.skip("should open modal", () => {
          // TODO: add when we have link binding working
          expect(false).is.eql(true);
        })
      })

    })
    describe("when experience delivery mechanism is api", function () {
      beforeEach(() => {
        cy.fixture("consent/test_banner_options.json").then((config) => {
          config.experience.delivery_mechanism = ExperienceDeliveryMechanism.API;
          cy.visitConsentDemo(config);
        })
      });
      it("does not render", () => {
        cy.get("div#fides-consent-banner").should("not.exist");
        cy.contains("button", "Accept Test").should("not.exist");
      })
      it.skip("hides the modal link", () => {
        // TODO: add when we have link binding working
        expect(false).is.eql(true);
      })
    });
  });
});
