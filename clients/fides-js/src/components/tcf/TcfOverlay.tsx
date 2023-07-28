import { h, FunctionComponent } from "preact";
import { useState, useCallback, useMemo } from "preact/hooks";
import ConsentBanner from "../ConsentBanner";

import {
  debugLog,
  hasActionNeededNotices,
  transformUserPreferenceToBoolean,
} from "../../lib/consent-utils";

import "../fides.css";
import Overlay from "../Overlay";
import { TcfConsentButtons } from "./TcfConsentButtons";
import { OverlayProps } from "../types";
import TcfTabs from "./TcfTabs";
import {
  TCFFeatureRecord,
  TCFPurposeRecord,
  TCFVendorRecord,
} from "../../lib/tcf/types";

const resolveConsentValueFromTcfModel = (
  model: TCFPurposeRecord | TCFFeatureRecord | TCFVendorRecord
) => {
  if (model.current_preference) {
    return transformUserPreferenceToBoolean(model.current_preference);
  }

  return transformUserPreferenceToBoolean(model.default_preference);
};

const getEnabledIds = (
  modelList:
    | TCFPurposeRecord[]
    | TCFFeatureRecord[]
    | TCFVendorRecord[]
    | undefined
) => {
  if (!modelList) {
    return [];
  }
  return modelList
    .map((model) => {
      const value = resolveConsentValueFromTcfModel(model);
      return { ...model, consentValue: value };
    })
    .filter((model) => model.consentValue)
    .map((model) => `${model.id}`);
};

export interface EnabledIds {
  purposes: string[];
  specialPurposes: string[];
  features: string[];
  specialFeatures: string[];
  vendors: string[];
}

export interface UpdateEnabledIds {
  newEnabledIds: string[];
  modelType: keyof EnabledIds;
}

const TcfOverlay: FunctionComponent<OverlayProps> = ({
  experience,
  options,
  cookie,
}) => {
  // TODO: should we get this from the cookie?
  const initialEnabledIds: EnabledIds = useMemo(() => {
    const {
      tcf_purposes: purposes,
      tcf_special_purposes: specialPurposes,
      tcf_features: features,
      tcf_special_features: specialFeatures,
      tcf_vendors: vendors,
    } = experience;

    return {
      purposes: getEnabledIds(purposes),
      specialPurposes: getEnabledIds(specialPurposes),
      features: getEnabledIds(features),
      specialFeatures: getEnabledIds(specialFeatures),
      vendors: getEnabledIds(vendors),
    };
  }, [experience]);

  const [draftIds, setDraftIds] = useState<EnabledIds>(initialEnabledIds);

  const showBanner = useMemo(
    () => experience.show_banner && hasActionNeededNotices(experience),
    [experience]
  );

  const handleUpdateDraftState = useCallback(
    ({ newEnabledIds, modelType }: UpdateEnabledIds) => {
      const updated = { ...draftIds, [modelType]: newEnabledIds };
      setDraftIds(updated);
    },
    [draftIds]
  );

  const handleUpdateAllPreferences = useCallback((enabledIds: EnabledIds) => {
    console.log({ enabledIds });
    // TODO: PATCH
  }, []);

  if (!experience.experience_config) {
    debugLog(options.debug, "No experience config found");
    return null;
  }
  const experienceConfig = experience.experience_config;

  return (
    <Overlay
      options={options}
      experience={experience}
      cookie={cookie}
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
                enabledKeys={draftIds}
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
          <TcfTabs
            experience={experience}
            enabledIds={draftIds}
            onChange={handleUpdateDraftState}
          />
          <TcfConsentButtons
            experience={experience}
            enabledKeys={draftIds}
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
