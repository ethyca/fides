import { h, FunctionComponent } from "preact";
import { useState, useCallback, useMemo } from "preact/hooks";
import ConsentBanner from "../ConsentBanner";

import {
  debugLog,
  hasActionNeededNotices,
  transformConsentToFidesUserPreference,
  transformUserPreferenceToBoolean,
} from "../../lib/consent-utils";

import "../fides.css";
import Overlay from "../Overlay";
import { TcfConsentButtons } from "./TcfConsentButtons";
import { OverlayProps } from "../types";

import type {
  TCFFeatureRecord,
  TCFFeatureSave,
  TCFPurposeRecord,
  TCFPurposeSave,
  TCFSpecialFeatureSave,
  TCFSpecialPurposeSave,
  TCFVendorRecord,
  TCFVendorSave,
  TcfSavePreferences,
} from "../../lib/tcf/types";

import { updateConsentPreferences } from "../../lib/preferences";
import {
  ButtonType,
  ConsentMethod,
  PrivacyExperience,
} from "../../lib/consent-types";
import { generateTcString } from "../../lib/tcf";
import { FidesCookie } from "../../lib/cookie";
import InitialLayer from "./InitialLayer";
import TcfTabs from "./TcfTabs";
import Button from "../Button";

const resolveConsentValueFromTcfModel = (
  model: TCFPurposeRecord | TCFFeatureRecord | TCFVendorRecord
) => {
  if (model.current_preference) {
    return transformUserPreferenceToBoolean(model.current_preference);
  }

  return transformUserPreferenceToBoolean(model.default_preference);
};

type TcfModels =
  | TCFPurposeRecord[]
  | TCFFeatureRecord[]
  | TCFVendorRecord[]
  | undefined;

type TcfSave =
  | TCFPurposeSave
  | TCFSpecialPurposeSave
  | TCFFeatureSave
  | TCFSpecialFeatureSave
  | TCFVendorSave;

const getEnabledIds = (modelList: TcfModels) => {
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
  systems: string[];
}

export interface UpdateEnabledIds {
  newEnabledIds: string[];
  modelType: keyof EnabledIds;
}

const transformTcfModelToTcfSave = ({
  modelList,
  enabledIds,
}: {
  modelList: TcfModels;
  enabledIds: string[];
}): TcfSave[] | null => {
  if (!modelList) {
    return [];
  }
  return modelList.map((model) => {
    const preference = transformConsentToFidesUserPreference(
      enabledIds.includes(`${model.id}`)
    );
    return {
      id: model.id,
      preference,
    };
  }) as TcfSave[];
};

const createTcfSavePayload = ({
  experience,
  enabledIds,
}: {
  experience: PrivacyExperience;
  enabledIds: EnabledIds;
}): TcfSavePreferences => ({
  purpose_preferences: transformTcfModelToTcfSave({
    modelList: experience.tcf_purposes,
    enabledIds: enabledIds.purposes,
  }) as TCFPurposeSave[],
  special_feature_preferences: transformTcfModelToTcfSave({
    modelList: experience.tcf_special_features,
    enabledIds: enabledIds.specialFeatures,
  }) as TCFSpecialFeatureSave[],
  vendor_preferences: transformTcfModelToTcfSave({
    modelList: experience.tcf_vendors,
    enabledIds: enabledIds.vendors,
  }) as TCFVendorSave[],
  system_preferences: transformTcfModelToTcfSave({
    modelList: experience.tcf_systems,
    enabledIds: enabledIds.systems,
  }) as TCFVendorSave[],
});

const updateCookie = async (
  oldCookie: FidesCookie,
  tcf: TcfSavePreferences,
  experience: PrivacyExperience
) => {
  const tcString = await generateTcString({
    tcStringPreferences: tcf,
    experience,
  });
  return { ...oldCookie, tcString };
};

const TcfOverlay: FunctionComponent<OverlayProps> = ({
  fidesRegionString,
  experience,
  options,
  cookie,
}) => {
  const initialEnabledIds: EnabledIds = useMemo(() => {
    const {
      tcf_purposes: purposes,
      tcf_special_purposes: specialPurposes,
      tcf_features: features,
      tcf_special_features: specialFeatures,
      tcf_vendors: vendors,
      tcf_systems: systems,
    } = experience;

    return {
      purposes: getEnabledIds(purposes),
      specialPurposes: getEnabledIds(specialPurposes),
      features: getEnabledIds(features),
      specialFeatures: getEnabledIds(specialFeatures),
      vendors: getEnabledIds(vendors),
      systems: getEnabledIds(systems),
    };
  }, [experience]);

  const [draftIds, setDraftIds] = useState<EnabledIds>(initialEnabledIds);

  const showBanner = useMemo(
    () => experience.show_banner && hasActionNeededNotices(experience),
    [experience]
  );

  const numVendors = useMemo(() => {
    const systemCount = experience.tcf_systems
      ? experience.tcf_systems.length
      : 0;
    const vendorCount = experience.tcf_vendors
      ? experience.tcf_vendors.length
      : 0;
    return systemCount + vendorCount;
  }, [experience]);

  const handleUpdateDraftState = useCallback(
    ({ newEnabledIds, modelType }: UpdateEnabledIds) => {
      const updated = { ...draftIds, [modelType]: newEnabledIds };
      setDraftIds(updated);
    },
    [draftIds]
  );

  const handleUpdateAllPreferences = useCallback(
    (enabledIds: EnabledIds) => {
      const tcf = createTcfSavePayload({ experience, enabledIds });
      updateConsentPreferences({
        consentPreferencesToSave: [],
        experienceId: experience.id,
        fidesApiUrl: options.fidesApiUrl,
        consentMethod: ConsentMethod.button,
        userLocationString: fidesRegionString,
        cookie,
        debug: options.debug,
        servedNotices: null, // TODO: served notices
        tcf,
        updateCookie: (oldCookie) => updateCookie(oldCookie, tcf, experience),
      });
      setDraftIds(enabledIds);
    },
    [cookie, experience, fidesRegionString, options]
  );

  const [activeTabIndex, setActiveTabIndex] = useState(0);

  if (!experience.experience_config) {
    debugLog(options.debug, "No experience config found");
    return null;
  }
  const experienceConfig = experience.experience_config;

  const goToVendorTab = () => {
    setActiveTabIndex(2);
  };

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
          >
            <InitialLayer experience={experience} />
            <button
              type="button"
              className="fides-link-button"
              onClick={() => {
                onManagePreferencesClick();
                goToVendorTab();
              }}
            >
              View our {numVendors} partner{numVendors === 1 ? "" : "s"}
            </button>
            <TcfConsentButtons
              experience={experience}
              onManagePreferencesClick={onManagePreferencesClick}
              onSave={(keys) => {
                handleUpdateAllPreferences(keys);
                onSave();
              }}
            />
          </ConsentBanner>
        ) : null
      }
      renderModalContent={({ onClose }) => {
        const onSave = (keys: EnabledIds) => {
          handleUpdateAllPreferences(keys);
          onClose();
        };
        return (
          <div>
            <TcfTabs
              experience={experience}
              enabledIds={draftIds}
              onChange={handleUpdateDraftState}
              activeTabIndex={activeTabIndex}
              onTabChange={setActiveTabIndex}
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
      }}
    />
  );
};

export default TcfOverlay;
