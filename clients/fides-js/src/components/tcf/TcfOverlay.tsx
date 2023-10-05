import { h, FunctionComponent } from "preact";
import { useState, useCallback, useMemo } from "preact/hooks";
import { TCString } from "@iabtechlabtcf/core";
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

import {
  type EnabledIds,
  LegalBasisForProcessingEnum,
  type TCFFeatureRecord,
  type TCFFeatureSave,
  type TCFPurposeRecord,
  type TCFPurposeSave,
  type TCFSpecialFeatureSave,
  type TCFSpecialPurposeSave,
  type TCFVendorRecord,
  type TCFVendorSave,
  type TcfSavePreferences,
} from "../../lib/tcf/types";

import { updateConsentPreferences } from "../../lib/preferences";
import {
  ButtonType,
  ConsentMethod,
  PrivacyExperience,
  UserConsentPreference,
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
import { vendorRecordsWithLegalBasis } from "../../lib/tcf/vendors";

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

const getVendorEnabledIds = (
  modelList: TCFVendorRecord[] | undefined,
  legalBasis: LegalBasisForProcessingEnum
) => {
  if (!modelList) {
    return [];
  }
  const records = vendorRecordsWithLegalBasis(modelList, legalBasis);
  if (legalBasis === LegalBasisForProcessingEnum.LEGITIMATE_INTERESTS) {
    // TODO: the backend should eventually return legint fields with a default preference of OPT_IN
    const modifiedRecords = records.map((record) => ({
      ...record,
      default_preference: UserConsentPreference.OPT_IN,
    }));
    return getEnabledIds(modifiedRecords);
  }
  return getEnabledIds(records);
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
  const systemIds = experience.tcf_systems
    ? experience.tcf_systems.map((s) => s.id)
    : [];
  const enabledSystemIds: string[] = [];
  const enabledVendorIds: string[] = [];
  enabledIds.vendorsConsent.forEach((id) => {
    if (systemIds.includes(id)) {
      enabledSystemIds.push(id);
    } else {
      enabledVendorIds.push(id);
    }
  });
  enabledIds.vendorsLegint.forEach((id) => {
    if (systemIds.includes(id)) {
      enabledSystemIds.push(id);
    } else {
      enabledVendorIds.push(id);
    }
  });

  return {
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
      // TODO: once the backend is storing this, we should send vendorsConsent
      // and vendorsLegint to separate fields (fidesplus1128)
      enabledIds: enabledVendorIds,
    }) as TCFVendorSave[],
    system_preferences: transformTcfModelToTcfSave({
      modelList: experience.tcf_systems,
      enabledIds: enabledSystemIds,
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
      tcf_purposes: purposes,
      tcf_special_purposes: specialPurposes,
      tcf_features: features,
      tcf_special_features: specialFeatures,
      tcf_vendors: vendors,
      tcf_systems: systems,
    } = experience;

    const vendorsAndSystems = [...(vendors || []), ...(systems || [])];
    let vendorsConsent = getVendorEnabledIds(
      vendorsAndSystems,
      LegalBasisForProcessingEnum.CONSENT
    );
    let vendorsLegint = getVendorEnabledIds(
      vendorsAndSystems,
      LegalBasisForProcessingEnum.LEGITIMATE_INTERESTS
    );

    // Initialize vendor values from the TC string if it's available. Neither the
    // backend nor the cookie store vendorsConsent or vendorsLegint yet, so we must
    // look at the string. (fidesplus#1128)
    if (cookie.tc_string && cookie.tc_string !== "") {
      const tcModel = TCString.decode(cookie.tc_string || "");
      vendorsConsent = [];
      vendorsLegint = [];
      tcModel.vendorConsents.forEach((consented, id) => {
        if (consented) {
          vendorsConsent.push(`${id}`);
        }
      });
      tcModel.vendorLegitimateInterests.forEach((consented, id) => {
        if (consented) {
          vendorsLegint.push(`${id}`);
        }
      });
      // but we still need to join system data to this
      const systemConsents = getVendorEnabledIds(
        systems,
        LegalBasisForProcessingEnum.CONSENT
      );
      const systemLegints = getVendorEnabledIds(
        systems,
        LegalBasisForProcessingEnum.LEGITIMATE_INTERESTS
      );
      vendorsConsent = [...vendorsConsent, ...systemConsents];
      vendorsLegint = [...vendorsLegint, ...systemLegints];
    }

    return {
      purposes: getEnabledIds(purposes),
      specialPurposes: getEnabledIds(specialPurposes),
      features: getEnabledIds(features),
      specialFeatures: getEnabledIds(specialFeatures),
      vendorsConsent,
      vendorsLegint,
    };
  }, [experience, cookie]);

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
