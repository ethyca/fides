export type ConsentBannerOptions = {
  // Whether or not debug log statements should be enabled
  debug?: boolean

  // Whether or not the banner should be displayed
  isEnabled?: boolean 

  // Display labels used for the banner text
  labels?: {
    bannerDescription?: string
    primaryButton?: string
    secondaryButton?: string
    tertiaryButton?: string
  }
};

/**
 * Get the configured options for the consent banner 
 */
export const getBannerOptions = (): ConsentBannerOptions => {
  return _globalBannerOptions;
};

/**
 * Initialize the Fides Consent Banner, with optional extraOptions to override defaults.
 * 
 * (see the type definition of ConsentBannerOptions for what options are available)
 */
export const banner = (extraOptions?: ConsentBannerOptions): void => {
  // If the user provides any extra options, override the defaults
  if (extraOptions !== undefined) {
    if (typeof extraOptions !== "object") {
      console.error("Invalid 'extraOptions' arg for Fides.banner(), ignoring", extraOptions);
    } else {
      setBannerOptions({ ...getBannerOptions(), ...extraOptions });
    }
  }

  const options: ConsentBannerOptions = getBannerOptions();
  debugLog("Initializing Fides consent banner...", options);

  if (options.isEnabled) {
    // TODO: wrap into displayBanner() and call after a getLocation() call first
    debugLog("Building Fides consent banner...");
    const banner: Node = buildBanner();

    debugLog("Building Fides consent banner styles...");
    const styles: Node = buildStyles();

    debugLog("Adding Fides consent banner CSS & HTML into the DOM...");
    document.head.appendChild(styles);
    document.body.appendChild(banner);
  }

  debugLog("Fides consent banner initialization complete!");
};

/**
 * Configuration options used for the consent banner. The default values (below)
 * will be mutated by the banner() function to override with any user-provided
 * options at runtime.
 * 
 * This is effectively a global variable, but we provide getter/setter functions
 * to make it seem safer and only export the getBannerOptions() one outside this
 * module.
 */
let _globalBannerOptions: ConsentBannerOptions = {
  debug: false,
  isEnabled: false,
  labels: {
    bannerDescription: "This website processes your data respectfully, so we require your consent to use cookies.",
    primaryButton: "Accept All",
    secondaryButton: "Reject All",
    tertiaryButton: "Manage Preferences",
  }
};

/**
 * Change the consent banner options.
 * 
 * WARNING: If called after `banner()` has already ran, many of these options
 * will no longer take effect!
 */
const setBannerOptions = (options: ConsentBannerOptions): void => {
  _globalBannerOptions = options;
};

/**
 * Wrapper around 'console.log' that only logs output when the 'debug' banner
 * option is truthy
 */
type ConsoleLogParameters = Parameters<typeof console.log>
const debugLog = (...args: ConsoleLogParameters): void => {
  if (getBannerOptions().debug) {
    console.log(...args) // TODO: use console.debug instead?
  }
};

/**
 * Builds the DOM elements for the consent banner (container, buttons, etc.) and
 * return a single div that can be added to the body. The expected HTML is:
 * 
 * <div>
 *   <div></div>
 *   <div>
 *     <button></button>
 *     <button></button>
 *     <button></button>
 *   </div>
 * </div>
 * 
 * To ease CSS customization, we also add descriptive classes to every element
 */
const buildBanner = (): Node => {
  const options: ConsentBannerOptions = getBannerOptions();

  // Create the overall banner container
  const banner = document.createElement("div");
  banner.id = "fides-consent-banner";
  banner.classList.add("fides-consent-banner");

  // Add the banner description
  const bannerDescription = document.createElement("div");
  bannerDescription.id = "fides-consent-banner-description";
  bannerDescription.classList.add("fides-consent-banner-description");
  bannerDescription.innerText = options.labels?.bannerDescription || "";
  banner.appendChild(bannerDescription);

  // Create the button container
  const buttonContainer = document.createElement("div");
  buttonContainer.id = "fides-consent-banner-buttons";
  buttonContainer.classList.add("fides-consent-banner-buttons");

  // Create the banner buttons
  const tertiaryButton = buildButton(
    "fides-consent-banner-button-tertiary",
    "fides-consent-banner-button-tertiary",
    options.labels?.tertiaryButton,
  );
  buttonContainer.appendChild(tertiaryButton);
  const secondaryButton = buildButton(
    "fides-consent-banner-button-secondary",
    "fides-consent-banner-button-secondary",
    options.labels?.secondaryButton,
  );
  buttonContainer.appendChild(secondaryButton);
  const primaryButton = buildButton(
    "fides-consent-banner-button-primary",
    "fides-consent-banner-button-primary",
    options.labels?.primaryButton,
  );
  buttonContainer.appendChild(primaryButton);

  // Add the button container to the banner
  banner.appendChild(buttonContainer);

  return banner;
};

/**
 * Builds a button DOM element with the given id, class name, and text label
 */
const buildButton = (id: string, className: string, label?: string): Node => {
  const options: ConsentBannerOptions = getBannerOptions();
  const button = document.createElement("button");
  button.id = id;
  button.innerHTML = label || "";
  button.classList.add("fides-consent-banner-button");
  button.classList.add(className);
  button.addEventListener("click", () => {
    debugLog(`Fides consent banner button clicked with id='${id}'`);
    // TODO: callback
  });
  return button;
};

/**
 * Default CSS styles for the banner
 */
const _defaultBannerStyle = `
:root {
  --fides-consent-banner-font-family: inherit;
  --fides-consent-banner-font-size: 16px;
  --fides-consent-banner-background: #fff;
  --fides-consent-banner-text-color: #24292f;
  --fides-consent-banner-padding: 0.75em 2em 1em;

  --fides-consent-banner-button-background: #eee;
  --fides-consent-banner-button-text-color: #24292f;
  --fides-consent-banner-button-hover-background: #ccc;
  --fides-consent-banner-button-border-radius: 4px;
  --fides-consent-banner-button-padding: 1em 1.5em;

  --fides-consent-banner-button-primary-background: #464b83;
  --fides-consent-banner-button-primary-text-color: #fff;
  --fides-consent-banner-button-primary-hover-background: #3f4375;

  --fides-consent-banner-button-secondary-background: var(--fides-consent-banner-button-background);
  --fides-consent-banner-button-secondary-text-color: var(--fides-consent-banner-button-text-color);
  --fides-consent-banner-button-secondary-hover-background: var(--fides-consent-banner-button-hover-background);

  --fides-consent-banner-button-tertiary-background: var(--fides-consent-banner-button-background);
  --fides-consent-banner-button-tertiary-text-color: var(--fides-consent-banner-button-text-color);
  --fides-consent-banner-button-tertiary-hover-background: var(--fides-consent-banner-button-hover-background);
}

div#fides-consent-banner {
  font-family: var(--fides-consent-banner-font-family);
  font-size: var(--fides-consent-banner-font-size);
  background: var(--fides-consent-banner-background);
  color: var(--fides-consent-banner-text-color);

  position: fixed;
  z-index: 1;
  width: 100%;
  bottom: 0;
  left: 0;
  box-sizing: border-box;
  padding: var(--fides-consent-banner-padding);

  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
}

div#fides-consent-banner-description {
  margin-top: 0.5em;
  margin-right: 2em;
  min-width: 40%;
  flex: 1;
}

div#fides-consent-banner-buttons {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
}

button.fides-consent-banner-button {
  display: inline-block;
  flex: auto;
  cursor: pointer;
  text-align: center;
  margin: 0;
  margin-top: 0.25em;
  margin-right: 0.25em;
  padding: var(--fides-consent-banner-button-padding);
  background: var(--fides-consent-banner-button-background);
  color: var(--fides-consent-banner-button-text-color);
  border: none;
  border-radius: var(--fides-consent-banner-button-border-radius);

  font-family: inherit;
  font-size: 100%;
  line-height: 1.15;
  text-decoration: none;
}

button.fides-consent-banner-button:hover {
  background: var(--fides-consent-banner-button-hover-background);
}

button.fides-consent-banner-button.fides-consent-banner-button-primary {
  background: var(--fides-consent-banner-button-primary-background);
  color: var(--fides-consent-banner-button-primary-text-color);
}

button.fides-consent-banner-button.fides-consent-banner-button-primary:hover {
  background: var(--fides-consent-banner-button-primary-hover-background);
}

button.fides-consent-banner-button.fides-consent-banner-button-secondary {
  background: var(--fides-consent-banner-button-secondary-background);
  color: var(--fides-consent-banner-button-secondary-text-color);
}

button.fides-consent-banner-button.fides-consent-banner-button-secondary:hover {
  background: var(--fides-consent-banner-button-secondary-hover-background);
}

button.fides-consent-banner-button.fides-consent-banner-button-tertiary {
  background: var(--fides-consent-banner-button-tertiary-background);
  color: var(--fides-consent-banner-button-tertiary-text-color);
}

button.fides-consent-banner-button.fides-consent-banner-button-tertiary:hover {
  background: var(--fides-consent-banner-button-tertiary-hover-background);
}
`

/**
 * Builds a 'style' element containing the CSS styles for the consent banner
 */
const buildStyles = (): Node => {
  const style = document.createElement("style");
  style.innerHTML = _defaultBannerStyle;
  return style;
};