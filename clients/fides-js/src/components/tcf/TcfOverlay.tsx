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
  EnabledIds,
  TCFFeatureRecord,
  TCFFeatureSave,
  TCFPurposeConsentRecord,
  TCFPurposeLegitimateInterestsRecord,
  TCFPurposeSave,
  TCFSpecialFeatureSave,
  TCFSpecialPurposeSave,
  TCFVendorSave,
  TcfSavePreferences,
  TCFConsentVendorRecord,
  TCFLegitimateInterestsVendorRecord,
  TcfModels,
} from "../../lib/tcf/types";

import { updateConsentPreferences } from "../../lib/preferences";
import {
  ButtonType,
  ConsentMethod,
  PrivacyExperience,
} from "../../lib/consent-types";
import { generateTcString } from "../../lib/tcf";
import {
  FidesCookie,
  transformTcfPreferencesToCookieKeys,
} from "../../lib/cookie";
import InitialLayer from "./InitialLayer";
import TcfTabs from "./TcfTabs";
import Button from "../Button";
import VendorInfoBanner from "./VendorInfoBanner";

const resolveConsentValueFromTcfModel = (
  model:
    | TCFPurposeConsentRecord
    | TCFPurposeLegitimateInterestsRecord
    | TCFFeatureRecord
    | TCFConsentVendorRecord
    | TCFLegitimateInterestsVendorRecord
) => {
  if (model.current_preference) {
    return transformUserPreferenceToBoolean(model.current_preference);
  }

  return transformUserPreferenceToBoolean(model.default_preference);
};

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
}): TcfSavePreferences => {
  // Because systems were combined with vendors to make the UI easier to work with,
  // we need to separate them out now (the backend treats them as separate entities).
  const systemIds = experience.tcf_system_relationships
    ? experience.tcf_system_relationships.map((s) => s.id)
    : [];
  const enabledConsentSystemIds: string[] = [];
  const enabledConsentVendorIds: string[] = [];
  const enabledLegintSystemIds: string[] = [];
  const enabledLegintVendorIds: string[] = [];
  enabledIds.vendorsConsent.forEach((id) => {
    if (systemIds.includes(id)) {
      enabledConsentSystemIds.push(id);
    } else {
      enabledConsentVendorIds.push(id);
    }
  });
  enabledIds.vendorsLegint.forEach((id) => {
    if (systemIds.includes(id)) {
      enabledLegintSystemIds.push(id);
    } else {
      enabledLegintVendorIds.push(id);
    }
  });

  return {
    purpose_consent_preferences: transformTcfModelToTcfSave({
      modelList: experience.tcf_consent_purposes,
      enabledIds: enabledIds.purposesConsent,
    }) as TCFPurposeSave[],
    purpose_legitimate_interests_preferences: transformTcfModelToTcfSave({
      modelList: experience.tcf_legitimate_interests_purposes,
      // TODO: fix enabledIds
      enabledIds: enabledIds.purposesLegint,
    }) as TCFPurposeSave[],
    special_feature_preferences: transformTcfModelToTcfSave({
      modelList: experience.tcf_special_features,
      enabledIds: enabledIds.specialFeatures,
    }) as TCFSpecialFeatureSave[],
    vendor_consent_preferences: transformTcfModelToTcfSave({
      modelList: experience.tcf_consent_vendors,
      enabledIds: enabledConsentVendorIds,
    }) as TCFVendorSave[],
    vendor_legitimate_interests_preferences: transformTcfModelToTcfSave({
      modelList: experience.tcf_legitimate_interests_vendors,
      enabledIds: enabledLegintVendorIds,
    }) as TCFVendorSave[],
    system_consent_preferences: transformTcfModelToTcfSave({
      modelList: experience.tcf_consent_systems,
      enabledIds: enabledConsentSystemIds,
    }) as TCFVendorSave[],
    system_legitimate_interests_preferences: transformTcfModelToTcfSave({
      modelList: experience.tcf_legitimate_interests_systems,
      enabledIds: enabledLegintSystemIds,
    }) as TCFVendorSave[],
  };
};

const updateCookie = async (
  oldCookie: FidesCookie,
  /**
   * `tcf` and `enabledIds` should represent the same data, where `tcf` is what is
   * sent to the backend, and `enabledIds` is what the FE uses. They have diverged
   * because the backend has not implemented separate vendor legint/consents yet.
   * Therefore, we need both entities right now, but eventually we should be able to
   * only use one. In other words, `enabledIds` has a field for `vendorsConsent` and
   * `vendorsLegint` but `tcf` only has `vendors`.
   */
  tcf: TcfSavePreferences,
  enabledIds: EnabledIds,
  experience: PrivacyExperience
): Promise<FidesCookie> => {
  const tcString = await generateTcString({
    tcStringPreferences: enabledIds,
    experience,
  });
  return {
    ...oldCookie,
    tc_string: tcString,
    tcf_consent: transformTcfPreferencesToCookieKeys(tcf),
  };
};

const TcfOverlay: FunctionComponent<OverlayProps> = ({
  fidesRegionString,
  experience,
  options,
  cookie,
}) => {
  const initialEnabledIds: EnabledIds = useMemo(() => {
    const {
      tcf_consent_purposes: consentPurposes = [],
      tcf_legitimate_interests_purposes: legintPurposes = [],
      tcf_special_purposes: specialPurposes = [],
      tcf_features: features = [],
      tcf_special_features: specialFeatures = [],
      tcf_consent_vendors: consentVendors = [],
      tcf_legitimate_interests_vendors: legintVendors = [],
      tcf_consent_systems: consentSystems = [],
      tcf_legitimate_interests_systems: legintSystems = [],
    } = experience;

    // Vendors and systems are the same to the FE, so we combine them here
    return {
      purposesConsent: getEnabledIds(consentPurposes),
      purposesLegint: getEnabledIds(legintPurposes),
      specialPurposes: getEnabledIds(specialPurposes),
      features: getEnabledIds(features),
      specialFeatures: getEnabledIds(specialFeatures),
      vendorsConsent: getEnabledIds([...consentVendors, ...consentSystems]),
      vendorsLegint: getEnabledIds([...legintVendors, ...legintSystems]),
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
        updateCookie: (oldCookie) =>
          updateCookie(oldCookie, tcf, enabledIds, experience),
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

  return (
    <Overlay
      options={options}
      experience={experience}
      cookie={cookie}
      onVendorPageClick={() => {
        setActiveTabIndex(2);
      }}
      renderBanner={({ isOpen, onClose, onSave, onManagePreferencesClick }) => {
        const goToVendorTab = () => {
          onManagePreferencesClick();
          setActiveTabIndex(2);
        };
        return showBanner ? (
          <ConsentBanner
            bannerIsOpen={isOpen}
            onClose={onClose}
            experience={experienceConfig}
            onVendorPageClick={goToVendorTab}
          >
            <InitialLayer experience={experience} />
            <VendorInfoBanner
              experience={experience}
              goToVendorTab={goToVendorTab}
            />
            <TcfConsentButtons
              experience={experience}
              onManagePreferencesClick={onManagePreferencesClick}
              onSave={(keys) => {
                handleUpdateAllPreferences(keys);
                onSave();
              }}
            />
          </ConsentBanner>
        ) : null;
      }}
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
