import { h } from "preact";
import WarningIcon from "./WarningIcon";
import { getConsentContext } from "../lib/consent-context";

const GpcInfo = () => {
  const context = getConsentContext();

  if (!context.globalPrivacyControl) {
    return null;
  }

  return (
    <div className="fides-gpc-banner">
      <div className="fides-gpc-warning">
        <WarningIcon />
      </div>
      <div>
        <p className="fides-gpc-header">Global Privacy Control detected</p>
        <p>
          Your global privacy control preference has been honored. You have been
          automatically opted out of data uses cases which adhere to global
          privacy control.
        </p>
      </div>
    </div>
  );
};

export default GpcInfo;
