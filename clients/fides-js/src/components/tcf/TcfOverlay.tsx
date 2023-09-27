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
  ConsentMechanism,
  ConsentMethod,
  LastServedNoticeSchema,
  PrivacyExperience,
} from "../../lib/consent-types";
import TcfModalContent from "./TcfModalContent";
import { generateTcString } from "../../lib/tcf";
import { FidesCookie } from "../../lib/cookie";
import InitialLayer from "./InitialLayer";
import { useConsentServed } from "../../lib/hooks";

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

type Category = "purpose" | "special_feature" | "vendor" | "system";
type NoticeSubMap = {
  [key: string]: string | number;
};

type NoticeMap = Record<Category, NoticeSubMap>;

const noticeMap = (servedNotices: LastServedNoticeSchema[]): NoticeMap => {
  const map: NoticeMap = {
    purpose: {},
    special_feature: {},
    vendor: {},
    system: {},
  };

  servedNotices.forEach((notice) => {
    (Object.keys(map) as Category[]).forEach((key) => {
      const value = notice[key as keyof LastServedNoticeSchema];
      if (value !== null)
        map[key][String(value)] = notice.served_notice_history_id;
    });
  });

  return map;
};

const transformTcfModelToTcfSave = ({
  modelList,
  enabledIds,
  noticeSubMap,
}: {
  modelList: TcfModels;
  enabledIds: string[];
  noticeSubMap: NoticeSubMap;
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
      served_notice_history_id: noticeSubMap[String(model.id)],
    };
  }) as TcfSave[];
};

const createTcfSavePayload = ({
  experience,
  enabledIds,
  servedNotices,
}: {
  experience: PrivacyExperience;
  enabledIds: EnabledIds;
  servedNotices: LastServedNoticeSchema[];
}): TcfSavePreferences => {
  const servedNoticeMap = noticeMap(servedNotices);
  return {
    purpose_preferences: transformTcfModelToTcfSave({
      modelList: experience.tcf_purposes,
      enabledIds: enabledIds.purposes,
      noticeSubMap: servedNoticeMap["purpose"],
    }) as TCFPurposeSave[],
    special_feature_preferences: transformTcfModelToTcfSave({
      modelList: experience.tcf_special_features,
      enabledIds: enabledIds.specialFeatures,
      noticeSubMap: servedNoticeMap["special_feature"],
    }) as TCFSpecialFeatureSave[],
    vendor_preferences: transformTcfModelToTcfSave({
      modelList: experience.tcf_vendors,
      enabledIds: enabledIds.vendors,
      noticeSubMap: servedNoticeMap["vendor"],
    }) as TCFVendorSave[],
    system_preferences: transformTcfModelToTcfSave({
      modelList: experience.tcf_systems,
      enabledIds: enabledIds.systems,
      noticeSubMap: servedNoticeMap["system"],
    }) as TCFVendorSave[],
  };
};

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

  const handleUpdateDraftState = useCallback(
    ({ newEnabledIds, modelType }: UpdateEnabledIds) => {
      const updated = { ...draftIds, [modelType]: newEnabledIds };
      setDraftIds(updated);
    },
    [draftIds]
  );

  const { servedNotices } = useConsentServed({
    notices: [],
    options,
    userGeography: fidesRegionString,
    acknowledgeMode: false,
    privacyExperience: experience,
  });

  const handleUpdateAllPreferences = useCallback(
    (enabledIds: EnabledIds, servedNotices: LastServedNoticeSchema[]) => {
      const tcf = createTcfSavePayload({
        experience,
        enabledIds,
        servedNotices,
      });
      updateConsentPreferences({
        consentPreferencesToSave: [],
        experienceId: experience.id,
        fidesApiUrl: options.fidesApiUrl,
        consentMethod: ConsentMethod.button,
        userLocationString: fidesRegionString,
        cookie,
        debug: options.debug,
        servedNotices: null,
        tcf,
        updateCookie: (oldCookie) => updateCookie(oldCookie, tcf, experience),
      });
      setDraftIds(enabledIds);
    },
    [cookie, experience, fidesRegionString, options]
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
      cookie={cookie}
      renderBanner={({ isOpen, onClose, onSave, onManagePreferencesClick }) =>
        showBanner ? (
          <ConsentBanner
            bannerIsOpen={isOpen}
            onClose={onClose}
            experience={experienceConfig}
          >
            <InitialLayer
              experience={experience}
              managePreferencesLink={
                <button
                  type="button"
                  onClick={onManagePreferencesClick}
                  className="fides-link-button"
                >
                  {experience.experience_config
                    ?.privacy_preferences_link_label || ""}
                </button>
              }
            />
            <TcfConsentButtons
              experience={experience}
              onManagePreferencesClick={onManagePreferencesClick}
              onSave={(keys) => {
                handleUpdateAllPreferences(keys, servedNotices);
                onSave();
              }}
            />
          </ConsentBanner>
        ) : null
      }
      renderModalContent={({ onClose }) => (
        <TcfModalContent
          experience={experience}
          draftIds={draftIds}
          onChange={handleUpdateDraftState}
          onSave={(keys) => {
            handleUpdateAllPreferences(keys, servedNotices);
            onClose();
          }}
        />
      )}
    />
  );
};

export default TcfOverlay;
