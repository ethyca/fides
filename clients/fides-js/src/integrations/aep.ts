/**
 * Adobe Experience Platform (AEP) Integration
 */

declare global {
  interface Window {
    alloy?: any;
    Visitor?: any;
    s?: any;
    adobe?: {
      optIn?: any;
      target?: any;
      analytics?: any;
    };
    _satellite?: any;
  }
}

/**
 * Structure for AEP diagnostic data
 */
export interface AEPDiagnostics {
  timestamp: string;
  alloy?: {
    configured: boolean;
    consent?: any;
    identity?: any;
    config?: any;
  };
  visitor?: {
    configured: boolean;
    marketingCloudVisitorID?: string;
    analyticsVisitorID?: string;
    audienceManagerLocationHint?: string;
    audienceManagerBlob?: string;
    optIn?: any;
    error?: string;
  };
  optIn?: {
    configured: boolean;
    categories?: {
      aa?: string;
      target?: string;
      aam?: string;
      ecid?: string;
    };
    isApproved?: {
      aa?: boolean;
      target?: boolean;
      aam?: boolean;
      ecid?: boolean;
    };
  };
  cookies?: {
    ecid?: string;
    amcv?: string;
    demdex?: string;
    dextp?: string;
    other?: Record<string, string>;
  };
  launch?: {
    configured: boolean;
    property?: string;
    environment?: string;
    buildDate?: string;
  };
  analytics?: {
    configured: boolean;
    reportSuite?: string;
    trackingServer?: string;
    visitorNamespace?: string;
  };
}

/**
 * AEP Integration API
 */
export interface AEPIntegration {
  /**
   * Dump all Adobe Experience Platform diagnostic information
   * Gathers data from alloy, Visitor API, optIn service, cookies, etc.
   */
  dump: () => AEPDiagnostics;
}

/**
 * Get ECID from cookies
 */
function getECIDFromCookies(): string | undefined {
  const cookies = document.cookie.split(';');

  // Look for AMCV cookie (contains ECID)
  const amcvCookie = cookies.find(c => c.trim().startsWith('AMCV_'));
  if (amcvCookie) {
    const value = amcvCookie.split('=')[1];
    if (value) {
      // ECID is typically stored as MCMID|<ecid>
      const match = value.match(/MCMID\|(\d+)/);
      if (match) {
        return match[1];
      }
    }
  }

  return undefined;
}

/**
 * Get all Adobe-related cookies
 */
function getAdobeCookies(): AEPDiagnostics['cookies'] {
  const cookies = document.cookie.split(';');
  const adobeCookies: Record<string, string> = {};

  cookies.forEach(cookie => {
    const [name, value] = cookie.trim().split('=');

    // Collect Adobe-specific cookies
    if (name.startsWith('AMCV_') ||
        name.startsWith('s_') ||
        name === 'demdex' ||
        name === 'dextp' ||
        name.includes('adobe') ||
        name.includes('mbox')) {
      adobeCookies[name] = value;
    }
  });

  return {
    ecid: getECIDFromCookies(),
    amcv: adobeCookies[Object.keys(adobeCookies).find(k => k.startsWith('AMCV_')) || ''],
    demdex: adobeCookies.demdex,
    dextp: adobeCookies.dextp,
    other: adobeCookies,
  };
}

/**
 * Get Adobe Web SDK (alloy) diagnostics
 */
function getAlloyDiagnostics(): AEPDiagnostics['alloy'] {
  if (typeof window.alloy !== 'function') {
    return { configured: false };
  }

  const diagnostics: AEPDiagnostics['alloy'] = {
    configured: true,
  };

  // Try to get consent state
  try {
    // Note: getConsent is not a standard alloy command, but some implementations have it
    // We'll just capture what we can
    diagnostics.consent = 'Unable to retrieve - requires custom implementation';
  } catch (e) {
    diagnostics.consent = 'Error retrieving consent';
  }

  return diagnostics;
}

/**
 * Get Visitor API (ECID) diagnostics
 */
function getVisitorDiagnostics(): AEPDiagnostics['visitor'] {
  if (!window.Visitor) {
    return { configured: false };
  }

  // Get visitor instance - requires adobe_mc_orgid
  let visitor;
  if (typeof window.Visitor.getInstance === 'function' && window.adobe_mc_orgid) {
    try {
      visitor = window.Visitor.getInstance(window.adobe_mc_orgid);
    } catch (error) {
      return {
        configured: false,
        error: error instanceof Error ? error.message : 'Failed to get Visitor instance'
      };
    }
  } else {
    return {
      configured: false,
      error: window.adobe_mc_orgid ? 'Visitor.getInstance not available' : 'adobe_mc_orgid not set'
    };
  }

  const diagnostics: AEPDiagnostics['visitor'] = {
    configured: true,
  };

  try {
    // Get Marketing Cloud Visitor ID (ECID)
    if (typeof visitor.getMarketingCloudVisitorID === 'function') {
      diagnostics.marketingCloudVisitorID = visitor.getMarketingCloudVisitorID();
    }

    // Get Analytics Visitor ID
    if (typeof visitor.getAnalyticsVisitorID === 'function') {
      diagnostics.analyticsVisitorID = visitor.getAnalyticsVisitorID();
    }

    // Get Audience Manager Location Hint
    if (typeof visitor.getAudienceManagerLocationHint === 'function') {
      diagnostics.audienceManagerLocationHint = visitor.getAudienceManagerLocationHint();
    }

    // Get Audience Manager Blob
    if (typeof visitor.getAudienceManagerBlob === 'function') {
      diagnostics.audienceManagerBlob = visitor.getAudienceManagerBlob();
    }

    // Get OptIn state from Visitor API
    if (visitor.optIn) {
      diagnostics.optIn = {
        isApproved: {
          aa: visitor.optIn.isApproved?.(visitor.optIn.Categories?.AA),
          target: visitor.optIn.isApproved?.(visitor.optIn.Categories?.TARGET),
          aam: visitor.optIn.isApproved?.(visitor.optIn.Categories?.AAM),
          ecid: visitor.optIn.isApproved?.(visitor.optIn.Categories?.ECID),
        },
      };
    }
  } catch (e) {
    // Silently handle errors
  }

  return diagnostics;
}

/**
 * Get OptIn Service diagnostics
 */
function getOptInDiagnostics(): AEPDiagnostics['optIn'] {
  if (!window.adobe?.optIn) {
    return { configured: false };
  }

  const { optIn } = window.adobe;
  const diagnostics: AEPDiagnostics['optIn'] = {
    configured: true,
    categories: {},
    isApproved: {},
  };

  try {
    // Get categories
    const categories = ['aa', 'target', 'aam', 'ecid'] as const;

    categories.forEach(category => {
      try {
        // Get approval status
        if (typeof optIn.isApproved === 'function') {
          diagnostics.isApproved![category] = optIn.isApproved(category);
        }

        // Get category state
        if (typeof optIn.fetchPermissions === 'function') {
          const permissions = optIn.fetchPermissions();
          if (permissions?.[category]) {
            diagnostics.categories![category] = permissions[category];
          }
        }
      } catch (e) {
        // Silently handle per-category errors
      }
    });
  } catch (e) {
    // Silently handle errors
  }

  return diagnostics;
}

/**
 * Get Adobe Launch diagnostics
 */
function getLaunchDiagnostics(): AEPDiagnostics['launch'] {
  if (!window._satellite) {
    return { configured: false };
  }

  const diagnostics: AEPDiagnostics['launch'] = {
    configured: true,
  };

  try {
    // Get Launch property info if available
    if (window._satellite.property) {
      diagnostics.property = window._satellite.property.name;
    }

    if (window._satellite.environment) {
      diagnostics.environment = window._satellite.environment.stage;
    }

    if (window._satellite.buildInfo) {
      diagnostics.buildDate = window._satellite.buildInfo.buildDate;
    }
  } catch (e) {
    // Silently handle errors
  }

  return diagnostics;
}

/**
 * Get Adobe Analytics diagnostics
 */
function getAnalyticsDiagnostics(): AEPDiagnostics['analytics'] {
  const s = window.s;

  if (!s) {
    return { configured: false };
  }

  const diagnostics: AEPDiagnostics['analytics'] = {
    configured: true,
  };

  try {
    if (s.account) {
      diagnostics.reportSuite = s.account;
    }

    if (s.trackingServer) {
      diagnostics.trackingServer = s.trackingServer;
    }

    if (s.visitorNamespace) {
      diagnostics.visitorNamespace = s.visitorNamespace;
    }
  } catch (e) {
    // Silently handle errors
  }

  return diagnostics;
}

/**
 * Initialize Adobe Experience Platform integration
 *
 * @returns AEP integration API with diagnostic methods
 *
 * @example
 * const aep = Fides.aep();
 * const diagnostics = aep.dump();
 * console.log(diagnostics);
 */
export const aep = (): AEPIntegration => {
  return {
    dump: (): AEPDiagnostics => {
      const diagnostics: AEPDiagnostics = {
        timestamp: new Date().toISOString(),
        alloy: getAlloyDiagnostics(),
        visitor: getVisitorDiagnostics(),
        optIn: getOptInDiagnostics(),
        cookies: getAdobeCookies(),
        launch: getLaunchDiagnostics(),
        analytics: getAnalyticsDiagnostics(),
      };

      return diagnostics;
    },
  };
};
