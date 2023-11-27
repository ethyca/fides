import { Fragment, FunctionComponent, h } from "preact";
import { useCallback, useMemo, useState } from "preact/hooks";
import ConsentBanner from "../ConsentBanner";
import PrivacyPolicyLink from "../PrivacyPolicyLink";

import {
  debugLog,
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
  TcfModels,
  TCFPurposeConsentRecord,
  TCFPurposeLegitimateInterestsRecord,
  TCFPurposeSave,
  TcfSavePreferences,
  TCFSpecialFeatureSave,
  TCFSpecialPurposeSave,
  TCFVendorConsentRecord,
  TCFVendorLegitimateInterestsRecord,
  TCFVendorSave,
} from "../../lib/tcf/types";

import { updateConsentPreferences } from "../../lib/preferences";
import {
  ButtonType,
  ConsentMethod,
  LastServedConsentSchema,
  PrivacyExperience,
  ServingComponent,
} from "../../lib/consent-types";
import { generateFidesString } from "../../lib/tcf";
import {
  FidesCookie,
  transformTcfPreferencesToCookieKeys,
} from "../../lib/cookie";
import InitialLayer from "./InitialLayer";
import TcfTabs from "./TcfTabs";
import Button from "../Button";
import { useConsentServed } from "../../lib/hooks";
import VendorInfoBanner from "./VendorInfoBanner";
import { dispatchFidesEvent } from "../../lib/events";

const resolveConsentValueFromTcfModel = (
  model:
    | TCFPurposeConsentRecord
    | TCFPurposeLegitimateInterestsRecord
    | TCFFeatureRecord
    | TCFVendorConsentRecord
    | TCFVendorLegitimateInterestsRecord
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

type Category =
  | "purpose_consent"
  | "purpose_legitimate_interests"
  | "special_feature"
  | "vendor_consent"
  | "vendor_legitimate_interests"
  | "system_consent"
  | "system_legitimate_interests";
type NoticeSubMap = {
  [key: string]: string | number;
};

type NoticeMap = Record<Category, NoticeSubMap>;

const noticeMap = (servedNotices: LastServedConsentSchema[]): NoticeMap => {
  const map: NoticeMap = {
    purpose_consent: {},
    purpose_legitimate_interests: {},
    special_feature: {},
    vendor_consent: {},
    vendor_legitimate_interests: {},
    system_consent: {},
    system_legitimate_interests: {},
  };

  servedNotices.forEach((notice) => {
    (Object.keys(map) as Category[]).forEach((key) => {
      const value = notice[key as keyof LastServedConsentSchema];
      if (value !== null) {
        map[key][String(value)] = notice.served_notice_history_id;
      }
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
  servedNotices: LastServedConsentSchema[];
}): TcfSavePreferences => {
  const servedNoticeMap = noticeMap(servedNotices);
  const {
    tcf_system_consents: consentSystems,
    tcf_system_legitimate_interests: legintSystems,
  } = experience;
  // Because systems were combined with vendors to make the UI easier to work with,
  // we need to separate them out now (the backend treats them as separate entities).
  const enabledConsentSystemIds: string[] = [];
  const enabledConsentVendorIds: string[] = [];
  const enabledLegintSystemIds: string[] = [];
  const enabledLegintVendorIds: string[] = [];
  enabledIds.vendorsConsent.forEach((id) => {
    if (consentSystems?.map((s) => s.id).includes(id)) {
      enabledConsentSystemIds.push(id);
    } else {
      enabledConsentVendorIds.push(id);
    }
  });
  enabledIds.vendorsLegint.forEach((id) => {
    if (legintSystems?.map((s) => s.id).includes(id)) {
      enabledLegintSystemIds.push(id);
    } else {
      enabledLegintVendorIds.push(id);
    }
  });

  return {
    purpose_consent_preferences: transformTcfModelToTcfSave({
      modelList: experience.tcf_purpose_consents,
      enabledIds: enabledIds.purposesConsent,
      noticeSubMap: servedNoticeMap.purpose_consent,
    }) as TCFPurposeSave[],
    purpose_legitimate_interests_preferences: transformTcfModelToTcfSave({
      modelList: experience.tcf_purpose_legitimate_interests,
      enabledIds: enabledIds.purposesLegint,
      noticeSubMap: servedNoticeMap.purpose_legitimate_interests,
    }) as TCFPurposeSave[],
    special_feature_preferences: transformTcfModelToTcfSave({
      modelList: experience.tcf_special_features,
      enabledIds: enabledIds.specialFeatures,
      noticeSubMap: servedNoticeMap.special_feature,
    }) as TCFSpecialFeatureSave[],
    vendor_consent_preferences: transformTcfModelToTcfSave({
      modelList: experience.tcf_vendor_consents,
      enabledIds: enabledConsentVendorIds,
      noticeSubMap: servedNoticeMap.vendor_consent,
    }) as TCFVendorSave[],
    vendor_legitimate_interests_preferences: transformTcfModelToTcfSave({
      modelList: experience.tcf_vendor_legitimate_interests,
      enabledIds: enabledLegintVendorIds,
      noticeSubMap: servedNoticeMap.vendor_legitimate_interests,
    }) as TCFVendorSave[],
    system_consent_preferences: transformTcfModelToTcfSave({
      modelList: experience.tcf_system_consents,
      enabledIds: enabledConsentSystemIds,
      noticeSubMap: servedNoticeMap.system_consent,
    }) as TCFVendorSave[],
    system_legitimate_interests_preferences: transformTcfModelToTcfSave({
      modelList: experience.tcf_system_legitimate_interests,
      enabledIds: enabledLegintSystemIds,
      noticeSubMap: servedNoticeMap.system_legitimate_interests,
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
  const tcString = await generateFidesString({
    tcStringPreferences: enabledIds,
    experience,
  });
  return {
    ...oldCookie,
    fides_string: tcString,
    tcf_consent: transformTcfPreferencesToCookieKeys(tcf),
    tcf_version_hash: experience.meta?.version_hash,
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
      tcf_purpose_consents: consentPurposes = [],
      tcf_purpose_legitimate_interests: legintPurposes = [],
      tcf_special_purposes: specialPurposes = [],
      tcf_features: features = [],
      tcf_special_features: specialFeatures = [],
      tcf_vendor_consents: consentVendors = [],
      tcf_vendor_legitimate_interests: legintVendors = [],
      tcf_system_consents: consentSystems = [],
      tcf_system_legitimate_interests: legintSystems = [],
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

  const { servedNotices } = useConsentServed({
    notices: [],
    options,
    userGeography: fidesRegionString,
    acknowledgeMode: false,
    privacyExperience: experience,
  });

  const handleUpdateAllPreferences = useCallback(
    (consentMethod: ConsentMethod, enabledIds: EnabledIds) => {
      const tcf = createTcfSavePayload({
        experience,
        enabledIds,
        servedNotices,
      });
      updateConsentPreferences({
        consentPreferencesToSave: [],
        experience,
        consentMethod,
        options,
        userLocationString: fidesRegionString,
        cookie,
        debug: options.debug,
        tcf,
        updateCookie: (oldCookie) =>
          updateCookie(oldCookie, tcf, enabledIds, experience),
      });
      setDraftIds(enabledIds);
    },
    [cookie, experience, fidesRegionString, options, servedNotices]
  );

  const [activeTabIndex, setActiveTabIndex] = useState(0);

  const dispatchOpenBannerEvent = useCallback(() => {
    dispatchFidesEvent("FidesUIShown", cookie, options.debug, {
      servingComponent: ServingComponent.TCF_BANNER,
    });
  }, [cookie, options.debug]);

  const dispatchOpenOverlayEvent = useCallback(() => {
    dispatchFidesEvent("FidesUIShown", cookie, options.debug, {
      servingComponent: ServingComponent.TCF_OVERLAY,
    });
  }, [cookie, options.debug]);

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
      onOpen={dispatchOpenOverlayEvent}
      renderBanner={({ isOpen, onClose, onSave, onManagePreferencesClick }) => {
        const goToVendorTab = () => {
          onManagePreferencesClick();
          setActiveTabIndex(2);
        };
        return (
          <ConsentBanner
            bannerIsOpen={isOpen}
            onOpen={dispatchOpenBannerEvent}
            onClose={onClose}
            experience={experienceConfig}
            onVendorPageClick={goToVendorTab}
            renderButtonGroup={({ isMobile }) => (
              <TcfConsentButtons
                experience={experience}
                onManagePreferencesClick={onManagePreferencesClick}
                onSave={(consentMethod: ConsentMethod, keys: EnabledIds) => {
                  handleUpdateAllPreferences(consentMethod, keys);
                  onSave();
                }}
                isMobile={isMobile}
                includePrivacyPolicy
              />
            )}
            className="fides-tcf-banner-container"
          >
            <div id="fides-tcf-banner-inner">
              <VendorInfoBanner
                experience={experience}
                goToVendorTab={goToVendorTab}
              />
              <InitialLayer experience={experience} />
            </div>
          </ConsentBanner>
        );
      }}
      renderModalContent={() => (
        <TcfTabs
          experience={experience}
          enabledIds={draftIds}
          onChange={(updatedIds) => {
            setDraftIds(updatedIds);
            dispatchFidesEvent("FidesUIChanged", cookie, options.debug);
          }}
          activeTabIndex={activeTabIndex}
          onTabChange={setActiveTabIndex}
        />
      )}
      renderModalFooter={({ onClose, isMobile }) => {
        const onSave = (consentMethod: ConsentMethod, keys: EnabledIds) => {
          handleUpdateAllPreferences(consentMethod, keys);
          onClose();
        };
        return (
          <Fragment>
            <TcfConsentButtons
              experience={experience}
              onSave={onSave}
              firstButton={
                <Button
                  buttonType={ButtonType.SECONDARY}
                  label={experience.experience_config?.save_button_label}
                  onClick={() => onSave(ConsentMethod.save, draftIds)}
                  className="fides-save-button"
                />
              }
              isMobile={isMobile}
            />
            <PrivacyPolicyLink experience={experience.experience_config} />
          </Fragment>
        );
      }}
    />
  );
};

export default TcfOverlay;
