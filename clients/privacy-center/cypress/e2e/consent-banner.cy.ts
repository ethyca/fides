import { CONSENT_COOKIE_NAME } from "fides-js";
import {ConsentBannerOptions, ConsentConfig, FidesConfig, FidesCookie} from "fides-js/src/fides";

// The fides-js-demo.html page is wired up to inject the
// `fidesConsentBannerOptions` into the Fides.init(...) function
declare global {
    interface Window {
        fidesConsentBannerOptions?: FidesConfig;
    }
}

// We define a custom Cypress command
declare global {
    namespace Cypress {
        interface Chainable {
            visitConsentDemo(
                consent?: ConsentConfig,
                bannerOptions?: ConsentBannerOptions
            ): Chainable<any>;
        }
    }
}


describe("Consent banner", () => {
    // Default options to use for all tests
    const testBannerOptions: FidesConfig = {
        consent: {
            options: [{
                cookieKeys: ["data_sales"],
                default: true,
                fidesDataUseKey: "data_use.sales"
            },{
                cookieKeys: ["tracking"],
                default: false,
                fidesDataUseKey: "advertising"
            }
            ]

        },
        bannerOptions: {
            debug: true, // enable debug logging
            labels: {
                bannerDescription: "This test website is overriding the banner description label.",
                primaryButton: "Accept Test",
                secondaryButton: "Reject Test",
                tertiaryButton: "Customize Test",
            }
        }
    };

    Cypress.Commands.add("visitConsentDemo", (consent?: ConsentConfig, bannerOptions?: ConsentBannerOptions) => {
        cy.visit("/fides-js-components-demo.html", {
            onBeforeLoad: (win) => {
                // eslint-disable-next-line no-param-reassign
                win.fidesConsentBannerOptions = {
                    consent: {
                        ...testBannerOptions.consent,
                        ...consent,
                    },
                    bannerOptions: {
                        ...testBannerOptions.bannerOptions,
                        ...bannerOptions,
                    }
                }
            },
        });
    })

    describe("when disabled", () => {
        beforeEach(() => {
            cy.visitConsentDemo(undefined, {isDisabled: true });
        });

        it("does not render", () => {
            cy.get("div#fides-consent-banner").should("not.exist");
            cy.contains("button", "Accept Test").should("not.exist");
        });
    })

    describe("when user has no saved consent cookie", () => {
        beforeEach(() => {
            cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        });

        describe("when banner is not disabled", () => {
            beforeEach(() => {
                cy.visitConsentDemo(undefined, {
                    isDisabled: false,
                    isGeolocationEnabled: false,
                });
            });

            it("should render the expected HTML banner", () => {
                cy.get("div#fides-consent-banner.fides-consent-banner").within(() => {
                    cy.get("div#fides-consent-banner-description.fides-consent-banner-description")
                        .contains("This test website is overriding the banner description label.");
                    cy.get("div#fides-consent-banner-buttons.fides-consent-banner-buttons").within(() => {
                        cy.get("button#fides-consent-banner-button-tertiary.fides-consent-banner-button.fides-consent-banner-button-tertiary")
                            .contains("Customize Test");
                        cy.get("button#fides-consent-banner-button-secondary.fides-consent-banner-button.fides-consent-banner-button-secondary")
                            .contains("Reject Test");
                        cy.get("button#fides-consent-banner-button-primary.fides-consent-banner-button.fides-consent-banner-button-primary")
                            .contains("Accept Test");
                        // Order matters - it should always be tertiary, then secondary, then primary!
                        cy.get("button").eq(0).should("have.id", "fides-consent-banner-button-tertiary")
                        cy.get("button").eq(1).should("have.id","fides-consent-banner-button-secondary")
                        cy.get("button").eq(2).should("have.id","fides-consent-banner-button-primary")
                    })
                });
            });

            it("should allow accepting all", () => {
                cy.contains("button", "Accept Test").should("be.visible").click();
                cy.waitUntilCookieExists(CONSENT_COOKIE_NAME).then(() => {
                    cy.getCookie(CONSENT_COOKIE_NAME).then(cookie => {
                        const cookieKeyConsent: FidesCookie = JSON.parse(
                            decodeURIComponent(cookie!.value)
                        );
                        expect(cookieKeyConsent.consent).property("data_sales").is.eql(true);
                        expect(cookieKeyConsent.consent).property("tracking").is.eql(true);
                    })
                    cy.contains("button", "Accept Test").should("not.be.visible");
                })
            });

            it("should support rejecting all consent options", () => {
                cy.contains("button", "Reject Test").should("be.visible").click();
                cy.waitUntilCookieExists(CONSENT_COOKIE_NAME).then(() => {
                    cy.getCookie(CONSENT_COOKIE_NAME).then(cookie => {
                        const cookieKeyConsent: FidesCookie = JSON.parse(
                            decodeURIComponent(cookie!.value)
                        );
                        expect(cookieKeyConsent.consent).property("data_sales").is.eql(false);
                        expect(cookieKeyConsent.consent).property("tracking").is.eql(false);
                    })
                })
            });

            it("should navigate to Privacy Center to manage consent options", () => {
                cy.contains("button", "Customize Test").should("be.visible").click();
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
        });
    });
});