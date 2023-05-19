import ConfigDrivenConsent from "./ConfigDrivenConsent";
import NoticeDrivenConsent from "./NoticeDrivenConsent";

const ConsentToggles = () => {
  // TODO: get this value from useSettings
  const isOverlayDisabled = false;

  if (isOverlayDisabled) {
    return <ConfigDrivenConsent />;
  }
  return <NoticeDrivenConsent />;
};

export default ConsentToggles;
