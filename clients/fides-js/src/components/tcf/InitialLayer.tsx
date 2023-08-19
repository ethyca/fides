import { h } from "preact";
import { useMemo } from "preact/hooks";
import { PrivacyExperience } from "../../lib/consent-types";

import {
  Stack,
  createStacks,
  getIdsNotRepresentedInStacks,
} from "../../lib/tcf/stacks";
import InitialLayerAccordion from "./InitialLayerAccordion";

// Temporarily hard coding this here until GVL json is integrated
const STACKS_JSON = {
  stacks: {
    "2": {
      id: 2,
      purposes: [2, 7],
      specialFeatures: [],
      name: "Advertising based on limited data and advertising measurement",
      description:
        "Advertising can be presented based on limited data. Advertising performance can be measured.",
    },
    "3": {
      id: 3,
      purposes: [2, 3, 4],
      specialFeatures: [],
      name: "Personalised advertising \n",
      description:
        "Advertising can be personalised based on your profile. Your activity on this service can be used to build or improve a profile about you for personalised advertising.\n",
    },
    "4": {
      id: 4,
      purposes: [2, 7, 9],
      specialFeatures: [],
      name: "Advertising based on limited data, advertising measurement, and understanding of the audiences",
      description:
        "Advertising can be presented based on limited data. Advertising performance can be measured. Reports can be generated based on your activity and those of others.",
    },
    "5": {
      id: 5,
      purposes: [2, 3, 7],
      specialFeatures: [],
      name: "Advertising based on limited data, personalised advertising profile, and advertising measurement\n\n",
      description:
        "Advertising can be presented based on limited data. Your activity on this service can be used to build or improve a profile about you for personalised advertising. Advertising performance can be measured.",
    },
    "6": {
      id: 6,
      purposes: [2, 4, 7],
      specialFeatures: [],
      name: "Selection of personalised advertising and advertising measurement",
      description:
        "Advertising can be personalised based on your profile. Advertising performance can be measured.",
    },
    "7": {
      id: 7,
      purposes: [2, 4, 7, 9],
      specialFeatures: [],
      name: "Selection of personalised advertising, advertising measurement, and audience research",
      description:
        "Advertising can be personalised based on your profile. Advertising performance can be measured. Reports can be generated based on your activity and those of others.",
    },
    "8": {
      id: 8,
      purposes: [2, 3, 4, 7],
      specialFeatures: [],
      name: "Personalised advertising and advertising measurement",
      description:
        "Advertising can be personalised based on your profile. Your activity on this service can be used to build or improve a profile about you for personalised advertising. Advertising performance can be measured.\n",
    },
    "9": {
      id: 9,
      purposes: [2, 3, 4, 7, 9],
      specialFeatures: [],
      name: "Personalised advertising, advertising measurement, and audience research",
      description:
        "Advertising can be personalised based on your profile. Your activity on this service can be used to build or improve a profile about you for personalised advertising. Advertising performance can be measured. Reports can be generated based on your activity and those of others.",
    },
    "10": {
      id: 10,
      purposes: [3, 4],
      specialFeatures: [],
      name: "Personalised advertising",
      description:
        "Advertising can be personalised based on your profile. Your activity on this service can be used to build or improve a profile about you for personalised advertising.",
    },
    "11": {
      id: 11,
      purposes: [5, 6],
      specialFeatures: [],
      name: "Personalised content",
      description:
        "Content can be personalised based on your profile. Your activity on this service can be used to build or improve a profile about you for personalised content.",
    },
    "12": {
      id: 12,
      purposes: [6, 8, 11],
      specialFeatures: [],
      name: "Selection of personalised content and content measurement",
      description:
        "Content can be personalised based on your profile. Content performance can be measured.\n",
    },
    "13": {
      id: 13,
      purposes: [6, 8, 11],
      specialFeatures: [],
      name: "Selection of personalised content, content measurement and audience research\n",
      description:
        "Content can be personalised based on your profile. Content performance can be measured. Reports can be generated based on your activity and those of others.Content can be personalised based on your profile. Content performance can be measured. Reports can be generated based on your activity and those of others. ",
    },
    "14": {
      id: 14,
      purposes: [5, 6, 8, 11],
      specialFeatures: [],
      name: "Personalised content and content measurement",
      description:
        "Content can be personalised based on your profile. Your activity on this service can be used to build or improve a profile about you for personalised content. Content performance can be measured.",
    },
    "15": {
      id: 15,
      purposes: [5, 6, 8, 9, 11],
      specialFeatures: [],
      name: "Personalised content, content measurement and audience research",
      description:
        "Content can be personalised based on your profile. Your activity on this service can be used to build or improve a profile about you for personalised content. Content performance can be measured. Reports can be generated based on your activity and those of others.",
    },
    "16": {
      id: 16,
      purposes: [5, 6, 8, 9, 10, 11],
      specialFeatures: [],
      name: "Personalised content, content measurement, audience research, and services development",
      description:
        "Content can be personalised based on your profile. Your activity on this service can be used to build or improve a profile about you for personalised content. Content performance can be measured. Reports can be generated based on your activity and those of others. Your activity on this service can help develop and improve products and services.",
    },
    "17": {
      id: 17,
      purposes: [7, 8, 9],
      specialFeatures: [],
      name: "Advertising and content measurement, and audience research",
      description:
        "Advertising and content performance can be measured. Reports can be generated based on your activity and those of others.",
    },
    "18": {
      id: 18,
      purposes: [7, 8],
      specialFeatures: [],
      name: "Advertising and content measurement\n\n",
      description: "Advertising and content performance can be measured.",
    },
    "19": {
      id: 19,
      purposes: [7, 9],
      specialFeatures: [],
      name: "Advertising measurement and audience research",
      description:
        "Advertising can be measured. Reports can be generated based on your activity and those of others.",
    },
    "20": {
      id: 20,
      purposes: [7, 8, 9, 10],
      specialFeatures: [],
      name: "Advertising and content measurement, audience research, and services development",
      description:
        "Advertising and content performance can be measured. Your activity on this service can help develop and improve products and services. Reports can be generated based on your activity and those of others. \n",
    },
    "21": {
      id: 21,
      purposes: [8, 9, 10],
      specialFeatures: [],
      name: "Content measurement, audience research and services development.",
      description:
        "Content performance can be measured. Reports can be generated based on your activity and those of others. Your activity on this service can help develop and improve products and services.",
    },
    "22": {
      id: 22,
      purposes: [8, 10],
      specialFeatures: [],
      name: "Content measurement and services development",
      description:
        "Content performance can be measured. Your activity on this service can help develop and improve products and services.\n",
    },
    "23": {
      id: 23,
      purposes: [2, 4, 6, 7, 8, 11],
      specialFeatures: [],
      name: "Selection of personalised advertising and content, advertising and content measurement",
      description:
        "Advertising and content can be personalised based on your profile. Advertising and content performance can be measured.\n",
    },
    "24": {
      id: 24,
      purposes: [2, 4, 6, 7, 8, 9, 11],
      specialFeatures: [],
      name: "Selection of personalised advertising and content, advertising and content measurement, and audience research",
      description:
        "Advertising and content can be personalised based on your profile. Advertising and content performance can be measured. Reports can be generated based on your activity and those of others. Data can be used to build or improve user experience, systems, and software.",
    },
    "25": {
      id: 25,
      purposes: [2, 3, 4, 5, 6, 7, 8, 11],
      specialFeatures: [],
      name: "Personalised advertising and content, advertising and content measurement",
      description:
        "Advertising and content can be personalised based on your profile. Your activity on this service can be used to build or improve a profile about you for personalised advertising or content. Advertising and content performance can be measured.",
    },
    "26": {
      id: 26,
      purposes: [2, 3, 4, 5, 6, 7, 8, 9, 11],
      specialFeatures: [],
      name: "Personalised advertising and content, advertising and content measurement, and audience research",
      description:
        "Advertising and content can be personalised based on your profile. Your activity on this service can be used to build or improve a profile about you for personalised advertising or content. Advertising and content performance can be measured. Reports can be generated based on your activity and those of others. \n",
    },
    "27": {
      id: 27,
      purposes: [3, 5],
      specialFeatures: [],
      name: "Personalised advertising and content profile",
      description:
        "Your activity on this service can be used to build or improve a profile about you for personalised advertising or content.\n",
    },
    "28": {
      id: 28,
      purposes: [2, 4, 6, 11],
      specialFeatures: [],
      name: "Selection of personalised advertising and content",
      description:
        "Advertising and content can be personalised based on your profile.",
    },
    "29": {
      id: 29,
      purposes: [2, 7, 8, 9],
      specialFeatures: [],
      name: "Advertising based on limited data, advertising and content measurement, and audience research\n\n",
      description:
        "Advertising can be presented based on limited data. Advertising and content performance can be measured. Reports can be generated based on your activity and those of others. \n",
    },
    "30": {
      id: 30,
      purposes: [2, 4, 5, 6, 7, 8, 9, 11],
      specialFeatures: [],
      name: "Selection of personalised advertising, personalised content, advertising and content measurement, and audience research\n",
      description:
        "Advertising and content can be personalised based on your profile. Your activity on this service can be used to build or improve a profile about you for personalised advertising or content. Advertising and content performance can be measured. Reports can be generated based on your activity and those of others.",
    },
    "31": {
      id: 31,
      purposes: [2, 4, 5, 6, 7, 8, 9, 10, 11],
      specialFeatures: [],
      name: "Selection of personalised advertising, personalised content, advertising and content measurement, audience research, and services development",
      description:
        "Advertising and content can be personalised based on your profile. Your activity on this service can be used to build or improve a profile about you for personalised content. Advertising and content performance can be measured. Reports can be generated based on your activity and those of others. Your activity on this service can help develop and improve products and services.\n",
    },
    "32": {
      id: 32,
      purposes: [2, 5, 6, 7, 8, 9, 11],
      specialFeatures: [],
      name: "Advertising based on limited data, personalised content, advertising and content measurement, and audience research",
      description:
        "Advertising can be presented based on limited data. Content can be personalised based on your profile. Your activity on this service can be used to build or improve a profile about you for personalised content. Advertising and content performance can be measured. Reports can be generated based on your activity and those of others. \n",
    },
    "33": {
      id: 33,
      purposes: [2, 5, 6, 7, 8, 9, 10, 11],
      specialFeatures: [],
      name: "Advertising based on limited data, personalised content, advertising and content measurement, audience research, and services development",
      description:
        "Advertising can be presented based on limited data. Content can be personalised based on your profile. Your activity on this service can be used to build or improve a profile about you for personalised content. Advertising and content performance can be measured. Reports can be generated based on your activity and those of others. Your activity on this service can help develop and improve products and services.",
    },
    "34": {
      id: 34,
      purposes: [2, 5, 6, 8, 9, 11],
      specialFeatures: [],
      name: "Advertising based on limited data, personalised content, content measurement, and audience research",
      description:
        "Advertising can be presented based on limited data. Content can be personalised based on your profile. Your activity on this service can be used to build or improve a profile about you for personalised content. Advertising and content performance can be measured. Reports can be generated based on your activity and those of others.",
    },
    "35": {
      id: 35,
      purposes: [2, 5, 6, 8, 9, 10, 11],
      specialFeatures: [],
      name: "Advertising based on limited data, personalised content, content measurement, audience research and services development",
      description:
        "Advertising can be presented based on limited data. Content can be personalised based on your profile. Your activity on this service can be used to build or improve a profile about you for personalised content. Content performance can be measured. Reports can be generated based on your activity and those of others. Your activity on this service can help develop and improve products and services.\n",
    },
    "36": {
      id: 36,
      purposes: [2, 5, 6, 7, 11],
      specialFeatures: [],
      name: "Advertising based on limited data, personalised content, and advertising measurement",
      description:
        "Advertising can be presented based on limited data. Content can be personalised based on your profile. Your activity on this service can be used to build or improve a profile about you for personalised content. Advertising performance can be measured.\n",
    },
    "37": {
      id: 37,
      purposes: [2, 5, 6, 7, 10, 11],
      specialFeatures: [],
      name: "Advertising based on limited data, personalised content, advertising measurement, and services development",
      description:
        "Advertising can be presented based on limited data. Content can be personalised based on your profile. Your activity on this service can be used to build or improve a profile about you for personalised content. Advertising performance can be measured. Your activity on this service can help develop and improve products and services.\n",
    },
    "38": {
      id: 38,
      purposes: [2, 3, 4, 7, 10],
      specialFeatures: [],
      name: "Personalised advertising, advertising measurement, and services development",
      description:
        "Advertising can be personalised based on your profile.Your activity on this service can be used to build or improve a profile about you for personalised advertising. Advertising performance can be measured. Your activity on this service can help develop and improve products and services.",
    },
    "39": {
      id: 39,
      purposes: [2, 3, 4, 7, 9, 10],
      specialFeatures: [],
      name: "Personalised advertising, advertising measurement, audience research and services development",
      description:
        "Advertising can be personalised based on your profile. Your activity on this service can be used to build or improve a profile about you for personalised advertising. Advertising performance can be measured. Reports can be generated based on your activity and those of others. Your activity on this service can help develop and improve products and services.",
    },
    "40": {
      id: 40,
      purposes: [2, 3, 4, 7, 8, 9, 10],
      specialFeatures: [],
      name: "Personalised advertising, advertising and content measurement, audience research and services development",
      description:
        "Advertising can be personalised based on your profile.Your activity on this service can be used to build or improve a profile about you for personalised advertising. Advertising and content performance can be measured. Reports can be generated based on your activity and those of others. Your activity on this service can help develop and improve products and services.\n",
    },
    "41": {
      id: 41,
      purposes: [2, 3, 4, 6, 7, 8, 9, 10, 11],
      specialFeatures: [],
      name: "Personalised advertising, selection of personalised content, advertising and content measurement, audience research and services development",
      description:
        "Advertising and content can be personalised based on your profile. Your activity on this service can be used to build or improve a profile about you for personalised advertising. Advertising and content performance can be measured. Reports can be generated based on your activity and those of others. Your activity on this service can help develop and improve products and services.\n",
    },
    "42": {
      id: 42,
      purposes: [2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
      specialFeatures: [],
      name: "Personalised advertising and content, advertising and content measurement, audience research and services development\n",
      description:
        "Advertising and content can be personalised based on your profile. Your activity on this service can be used to build or improve a profile about you for personalised advertising and content. Advertising and content performance can be measured. Reports can be generated based on your activity and those of others. Your activity on this service can help develop and improve products and services.",
    },
    "43": {
      id: 43,
      purposes: [8, 11],
      specialFeatures: [],
      name: "Content based on limited data and content measurement",
      description:
        "Content can be selected based on limited data. Content performance can be measured.",
    },
    "1": {
      id: 1,
      purposes: [],
      specialFeatures: [1, 2],
      name: "Precise geolocation data, and identification through device scanning",
      description:
        "Precise geolocation and information about device characteristics can be used.\n\n",
    },
  },
};

const STACKS: Record<string, Stack> = STACKS_JSON.stacks;

const InitialLayer = ({ experience }: { experience: PrivacyExperience }) => {
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
        {stacks.map((s) => (
          <InitialLayerAccordion
            key={s.id}
            title={s.name}
            description={s.description}
          />
        ))}
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
            // TODO: features are still being worked on in the backend
            title={sf.name || ""}
            description=""
          />
        ))}
      </div>
    </div>
  );
};

export default InitialLayer;
