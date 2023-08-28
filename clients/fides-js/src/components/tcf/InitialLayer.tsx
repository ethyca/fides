import { VNode, h } from "preact";
import { useMemo } from "preact/hooks";
import { PrivacyExperience } from "../../lib/consent-types";

import {
  Stack,
  createStacks,
  getIdsNotRepresentedInStacks,
} from "../../lib/tcf/stacks";
import GVL_JSON from "../../lib/tcf/gvl.json";
import InitialLayerAccordion from "./InitialLayerAccordion";

const STACKS: Record<string, Stack> = GVL_JSON.stacks;

const InitialLayer = ({
  experience,
  managePreferencesLink,
}: {
  experience: PrivacyExperience;
  managePreferencesLink: VNode;
}) => {
  const purposeIds = useMemo(
    () =>
      experience.tcf_purposes ? experience.tcf_purposes.map((p) => p.id) : [],
    [experience.tcf_purposes]
  );

  const specialFeatureIds = useMemo(
    () =>
      experience.tcf_special_features
        ? experience.tcf_special_features.map((sf) => sf.id)
        : [],
    [experience.tcf_special_features]
  );

  const stacks = useMemo(
    () =>
      createStacks({
        purposeIds,
        specialFeatureIds,
        stacks: STACKS,
      }),
    [purposeIds, specialFeatureIds]
  );

  const purposes = useMemo(() => {
    if (!experience.tcf_purposes) {
      return [];
    }
    const ids = getIdsNotRepresentedInStacks({
      ids: purposeIds,
      stacks,
      modelType: "purposes",
    });
    return experience.tcf_purposes.filter(
      (purpose) => ids.indexOf(purpose.id) !== -1
    );
  }, [stacks, purposeIds, experience.tcf_purposes]);

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
          const stackPurposes = experience.tcf_purposes
            ? experience.tcf_purposes.filter(
                (p) => s.purposes.indexOf(p.id) !== -1
              )
            : [];
          return (
            <InitialLayerAccordion
              key={s.id}
              title={s.name}
              description={s.description}
              purposes={stackPurposes}
              managePreferencesLink={managePreferencesLink}
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
            managePreferencesLink={managePreferencesLink}
          />
        ))}
      </div>
      <div>
        {specialFeatures.map((sf) => (
          <InitialLayerAccordion
            key={sf.id}
            // TODO: features are still being worked on in the backend
            title={sf.name || ""}
            description=""
            managePreferencesLink={managePreferencesLink}
          />
        ))}
      </div>
    </div>
  );
};

export default InitialLayer;
