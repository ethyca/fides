import { h } from "preact";
import { useState } from "preact/hooks";
import TcfTabs from "./TcfTabs";
import { TcfConsentButtons } from "./TcfConsentButtons";
import { ButtonType, PrivacyExperience } from "../../lib/consent-types";
import type { EnabledIds, UpdateEnabledIds } from "./TcfOverlay";
import Button from "../Button";
import InitialLayer from "./InitialLayer";

const BackButton = ({ onClick }: { onClick: () => void }) => (
  <button type="button" className="fides-back-button" onClick={onClick}>
    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="none">
      <path
        fill="#2D3748"
        d="M3.914 5.5H10v1H3.914l2.682 2.682-.707.707L2 6l3.889-3.889.707.707L3.914 5.5Z"
      />
    </svg>
    Back
  </button>
);

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
        <InitialLayer experience={experience} />
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
      <BackButton onClick={() => setIsInitialLayer(true)} />
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
