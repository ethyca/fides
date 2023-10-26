import { h } from "preact";
import { useMemo } from "preact/hooks";
import { PrivacyExperience } from "../../lib/consent-types";

import {
  createStacks,
  getIdsNotRepresentedInStacks,
} from "../../lib/tcf/stacks";
import InitialLayerAccordion from "./InitialLayerAccordion";

import { getUniquePurposeRecords } from "../../lib/tcf/purposes";

const InitialLayer = ({ experience }: { experience: PrivacyExperience }) => {
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
    if (!experience.gvl || Object.keys(experience.gvl).length === 0) {
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
