import { h, FunctionComponent } from "preact";
import { useState, useCallback, useMemo } from "preact/hooks";
import ConsentBanner from "../ConsentBanner";

import { debugLog, hasActionNeededNotices } from "../../lib/consent-utils";

import "../fides.css";
import Overlay from "../Overlay";
import { TcfConsentButtons } from "../ConsentButtons";
import { OverlayProps } from "../types";

const TcfOverlay: FunctionComponent<OverlayProps> = ({
  experience,
  options,
  cookie,
}) => {
  // TODO: how will we initialize TCF data?
  const initialEnabledKeys = useMemo(
    () => Object.keys(cookie.consent).filter((key) => cookie.consent[key]),
    [cookie.consent]
  );

  const [draftEnabledKeys] = useState<Array<string>>(initialEnabledKeys);

  const showBanner = useMemo(
    () => experience.show_banner && hasActionNeededNotices(experience),
    [experience]
  );

  // TODO: figure out how keys will work here
  const handleUpdatePurposes = useCallback(() => {}, []);
  const handleUpdateFeatures = useCallback(() => {}, []);
  const handleUpdateVendors = useCallback(() => {}, []);

  const handleUpdateAllPreferences = useCallback(
    (enabledKeys: string[]) => {
      console.log({ enabledKeys });
      handleUpdatePurposes();
      handleUpdateFeatures();
      handleUpdateVendors();
    },
    [handleUpdatePurposes, handleUpdateFeatures, handleUpdateVendors]
  );

  if (!experience.experience_config) {
    debugLog(options.debug, "No experience config found");
    return null;
  }
  const experienceConfig = experience.experience_config;

  return (
    <Overlay
      options={options}
      experience={experience}
      renderBanner={({ isOpen, onClose, onSave, onManagePreferencesClick }) =>
        showBanner ? (
          <ConsentBanner
            bannerIsOpen={isOpen}
            onClose={onClose}
            experience={experienceConfig}
            buttonGroup={
              <TcfConsentButtons
                experience={experience}
                onManagePreferencesClick={onManagePreferencesClick}
                enabledKeys={draftEnabledKeys}
                onSave={(keys) => {
                  handleUpdateAllPreferences(keys);
                  onSave();
                }}
              />
            }
          />
        ) : null
      }
      renderModalContent={({ onClose }) => (
        <div>
          <div>TCF TODO</div>
          <TcfConsentButtons
            experience={experience}
            enabledKeys={draftEnabledKeys}
            onSave={(keys) => {
              handleUpdateAllPreferences(keys);
              onClose();
            }}
            isInModal
          />
        </div>
      )}
    />
  );
};

export default TcfOverlay;
