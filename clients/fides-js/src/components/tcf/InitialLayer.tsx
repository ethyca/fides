import { h } from "preact";
import { useMemo } from "preact/hooks";

import { PrivacyExperience } from "../../lib/consent-types";
import type { I18n } from "../../lib/i18n";
import { getUniquePurposeRecords } from "../../lib/tcf/purposes";
import {
  createStacks,
  getIdsNotRepresentedInStacks,
} from "../../lib/tcf/stacks";
import { GVLTranslationJson } from "../../lib/tcf/types";

import InitialLayerAccordion from "./InitialLayerAccordion";

const InitialLayer = ({
  experience,
  i18n,
  gvlTranslation,
}: {
  experience: PrivacyExperience;
  i18n: I18n;
  gvlTranslation?: GVLTranslationJson;
}) => {
  const {
    tcf_purpose_consents: consentPurposes = [],
    tcf_purpose_legitimate_interests: legintPurposes = [],
    tcf_special_features: experienceSpecialFeatures = [],
  } = experience;

  const { uniquePurposeIds, uniquePurposes } = useMemo(
    () => getUniquePurposeRecords({ consentPurposes, legintPurposes }),
    [consentPurposes, legintPurposes]
  );

  const specialFeatureIds = useMemo(
    () => experienceSpecialFeatures.map((sf) => sf.id),
    [experienceSpecialFeatures]
  );

  const stacks = useMemo(() => {
    if (!gvlTranslation || !gvlTranslation.stacks) {
      return [];
    }
    return createStacks({
      purposeIds: uniquePurposeIds,
      specialFeatureIds,
      stacks: gvlTranslation.stacks,
    });
  }, [uniquePurposeIds, specialFeatureIds, gvlTranslation]);

  const purposes = useMemo(() => {
    const ids = getIdsNotRepresentedInStacks({
      ids: uniquePurposeIds,
      stacks,
      modelType: "purposes",
    });

    return uniquePurposes.filter((p) => ids.includes(p.id));
  }, [stacks, uniquePurposeIds, uniquePurposes]);

  const specialFeatures = useMemo(() => {
    if (!experience.tcf_special_features) {
      return [];
    }
    const ids = getIdsNotRepresentedInStacks({
      ids: specialFeatureIds,
      stacks,
      modelType: "specialFeatures",
    });
    return experience.tcf_special_features.filter(
      (sf) => ids.indexOf(sf.id) !== -1
    );
  }, [stacks, specialFeatureIds, experience.tcf_special_features]);

  return (
    <div className="fides-tcf-stacks-container">
      <div>
        {stacks.map((s) => {
          const stackPurposes = uniquePurposes.filter(
            (p) => s.purposes.indexOf(p.id) !== -1
          );
          return (
            <InitialLayerAccordion
              key={s.id}
              i18n={i18n}
              title={s.name}
              description={s.description}
              purposes={stackPurposes}
            />
          );
        })}
      </div>
      <div>
        {purposes.map((p) => (
          <InitialLayerAccordion
            key={p.id}
            i18n={i18n}
            title={p.name}
            description={p.description}
          />
        ))}
      </div>
      <div>
        {specialFeatures.map((sf) => (
          <InitialLayerAccordion
            key={sf.id}
            i18n={i18n}
            title={sf.name}
            description={sf.description}
          />
        ))}
      </div>
    </div>
  );
};

export default InitialLayer;
