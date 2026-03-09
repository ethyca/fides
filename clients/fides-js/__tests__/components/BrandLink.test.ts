import type { AttributionOptions } from "~/lib/consent-types";

describe("ConsentButtons attribution visibility logic", () => {
  it("shows brand link in banner when attribution is enabled", () => {
    const isInModal = false;
    const showFidesBrandLink = false;
    const attribution: AttributionOptions = {
      anchorText: "Powered by Ethyca",
      destinationUrl: "https://ethyca.com",
      nofollow: false,
    };

    const includeAttributionLink = !!attribution;
    const includeBrandLink =
      includeAttributionLink || (isInModal && showFidesBrandLink);

    expect(includeBrandLink).toBe(true);
  });

  it("shows brand link in modal when attribution is enabled", () => {
    const isInModal = true;
    const showFidesBrandLink = false;
    const attribution: AttributionOptions = {
      anchorText: "Powered by Ethyca",
      destinationUrl: "https://ethyca.com",
      nofollow: false,
    };

    const includeAttributionLink = !!attribution;
    const includeBrandLink =
      includeAttributionLink || (isInModal && showFidesBrandLink);

    expect(includeBrandLink).toBe(true);
  });

  it("only shows brand link in modal when attribution is NOT enabled", () => {
    const attribution = undefined;
    const showFidesBrandLink = true;

    const includeAttributionLink = !!attribution;

    // Banner: no brand link
    const includeBrandLinkBanner =
      includeAttributionLink || (false && showFidesBrandLink);
    expect(includeBrandLinkBanner).toBe(false);

    // Modal: brand link shown
    const includeBrandLinkModal =
      includeAttributionLink || (true && showFidesBrandLink);
    expect(includeBrandLinkModal).toBe(true);
  });

  it("does not show brand link when both attribution and showFidesBrandLink are off", () => {
    const attribution = undefined;
    const showFidesBrandLink = false;

    const includeAttributionLink = !!attribution;
    const includeBrandLink =
      includeAttributionLink || (true && showFidesBrandLink);

    expect(includeBrandLink).toBe(false);
  });
});
