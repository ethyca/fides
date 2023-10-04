import { h } from "preact";
import { useMemo } from "preact/hooks";
import { PrivacyExperience } from "../../lib/consent-types";

import {
  createStacks,
  getIdsNotRepresentedInStacks,
} from "../../lib/tcf/stacks";
import InitialLayerAccordion from "./InitialLayerAccordion";
import {
  TCFPurposeConsentRecord,
  TCFPurposeLegitimateInterestsRecord,
} from "../../lib/tcf/types";

const InitialLayer = ({ experience }: { experience: PrivacyExperience }) => {
  const {
    tcf_consent_purposes: consentPurposes = [],
    tcf_legitimate_interests_purposes: legintPurposes = [],
    tcf_special_features: experienceSpecialFeatures = [],
  } = experience;

  const uniquePurposeIds = useMemo(() => {
    const consents = consentPurposes.map((p) => p.id);
    const legints = legintPurposes.map((p) => p.id) ?? [];
    const ids = new Set([...consents, ...legints]);
    return Array.from(ids);
  }, [consentPurposes, legintPurposes]);

  const specialFeatureIds = useMemo(
    () => experienceSpecialFeatures.map((sf) => sf.id),
    [experienceSpecialFeatures]
  );

  const uniquePurposes = useMemo(() => {
    const purposes: (
      | TCFPurposeConsentRecord
      | TCFPurposeLegitimateInterestsRecord
    )[] = [];
    uniquePurposeIds.forEach((id) => {
      const consent = consentPurposes.find((p) => p.id === id);
      const legint = legintPurposes.find((p) => p.id === id);
      if (consent) {
        purposes.push(consent);
      } else if (legint) {
        purposes.push(legint);
      }
    });
    return purposes;
  }, [uniquePurposeIds, consentPurposes, legintPurposes]);

  const stacks = useMemo(() => {
    if (!experience.gvl) {
      return [];
    }
    return createStacks({
      purposeIds: uniquePurposeIds,
      specialFeatureIds,
      stacks: experience.gvl.stacks,
    });
  }, [uniquePurposeIds, specialFeatureIds, experience.gvl]);

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
    <div>
      <div>
        {stacks.map((s) => {
          const stackPurposes = uniquePurposes.filter(
            (p) => s.purposes.indexOf(p.id) !== -1
          );
          return (
            <InitialLayerAccordion
              key={s.id}
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
            title={p.name}
            description={p.description}
          />
        ))}
      </div>
      <div>
        {specialFeatures.map((sf) => (
          <InitialLayerAccordion
            key={sf.id}
            title={sf.name}
            description={sf.description}
          />
        ))}
      </div>
    </div>
  );
};

export default InitialLayer;
