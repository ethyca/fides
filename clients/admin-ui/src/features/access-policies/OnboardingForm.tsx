import { Flex, Form } from "fidesui";
import { useState } from "react";

import DataUseCardsSection from "./DataUseCardsSection";
import IndustryGeographySection from "./IndustryGeographySection";
import PrivacyPolicySection from "./PrivacyPolicySection";
import RefiningScanInfoBox from "./RefiningScanInfoBox";
import { OnboardingFormState } from "./types";

const INITIAL_STATE: OnboardingFormState = {
  industry: null,
  geography: null,
  selectedDataUses: [],
  policyUrl: "",
};

const OnboardingForm = () => {
  const [formState, setFormState] =
    useState<OnboardingFormState>(INITIAL_STATE);

  const handleToggleDataUse = (id: string) => {
    setFormState((prev) => ({
      ...prev,
      selectedDataUses: prev.selectedDataUses.includes(id)
        ? prev.selectedDataUses.filter((d) => d !== id)
        : [...prev.selectedDataUses, id],
    }));
  };

  return (
    <div className="max-w-3xl">
      <Form layout="vertical">
        <Flex vertical gap={32}>
          <IndustryGeographySection
            industry={formState.industry}
            geography={formState.geography}
            onIndustryChange={(value) =>
              setFormState((prev) => ({
                ...prev,
                industry: value,
                selectedDataUses: [],
              }))
            }
            onGeographyChange={(value) =>
              setFormState((prev) => ({ ...prev, geography: value }))
            }
          />

          <DataUseCardsSection
            industry={formState.industry}
            selectedDataUses={formState.selectedDataUses}
            onToggleDataUse={handleToggleDataUse}
          />

          <PrivacyPolicySection
            policyUrl={formState.policyUrl}
            onUrlChange={(url) =>
              setFormState((prev) => ({ ...prev, policyUrl: url }))
            }
          />

          <RefiningScanInfoBox industry={formState.industry} />
        </Flex>
      </Form>
    </div>
  );
};

export default OnboardingForm;
