import { h } from "preact";
import { useState } from "preact/hooks";
import TcfTabs from "./TcfTabs";
import { TcfConsentButtons } from "./TcfConsentButtons";
import { ButtonType, PrivacyExperience } from "../../lib/consent-types";
import type { EnabledIds, UpdateEnabledIds } from "./TcfOverlay";
import Button from "../Button";

const TcfModalContent = ({
  experience,
  draftIds,
  onChange,
  onSave,
}: {
  experience: PrivacyExperience;
  draftIds: EnabledIds;
  onChange: (payload: UpdateEnabledIds) => void;
  onSave: (keys: EnabledIds) => void;
}) => {
  const [isInitialLayer, setIsInitialLayer] = useState(true);
  if (isInitialLayer) {
    return (
      <div>
        initial layer
        <TcfConsentButtons
          experience={experience}
          onSave={onSave}
          firstButton={
            <Button
              buttonType={ButtonType.SECONDARY}
              label={
                experience.experience_config?.privacy_preferences_link_label
              }
              onClick={() => setIsInitialLayer(false)}
            />
          }
        />
      </div>
    );
  }
  return (
    <div>
      <TcfTabs
        experience={experience}
        enabledIds={draftIds}
        onChange={onChange}
      />
      <TcfConsentButtons
        experience={experience}
        onSave={onSave}
        firstButton={
          <Button
            buttonType={ButtonType.SECONDARY}
            label={experience.experience_config?.save_button_label}
            onClick={() => onSave(draftIds)}
          />
        }
      />
    </div>
  );
};

export default TcfModalContent;
