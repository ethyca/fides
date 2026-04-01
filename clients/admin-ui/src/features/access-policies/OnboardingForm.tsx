import { Col, Flex, Form, Row, Select } from "fidesui";
import { useState } from "react";

import { useGetOnboardingDataUsesQuery } from "./access-policies.slice";
import { GEOGRAPHY_OPTIONS, INDUSTRY_OPTIONS } from "./constants";
import DataUseCardsSection from "./DataUseCardsSection";
import PrivacyPolicySection from "./PrivacyPolicySection";
import { OnboardingFormState } from "./types";

const INITIAL_STATE: OnboardingFormState = {
  industry: null,
  geographies: [],
  selectedDataUses: [],
  policyUrl: "",
};

const OnboardingForm = () => {
  const [formState, setFormState] =
    useState<OnboardingFormState>(INITIAL_STATE);

  const { data, isLoading, isFetching } = useGetOnboardingDataUsesQuery(
    { industry: formState.industry!, geographies: formState.geographies },
    { skip: !formState.industry || formState.geographies.length === 0 },
  );

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
          <Row gutter={24}>
            <Col span={12}>
              <Form.Item
                label="Business vertical / industry"
                required
                htmlFor="industry-select"
                className="!mb-0"
              >
                <Select
                  id="industry-select"
                  aria-label="Business vertical / industry"
                  className="w-full"
                  placeholder="Select industry"
                  value={formState.industry}
                  onChange={(value) =>
                    setFormState((prev) => ({
                      ...prev,
                      industry: value,
                      selectedDataUses: [],
                    }))
                  }
                  options={INDUSTRY_OPTIONS}
                  allowClear
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="Geography"
                htmlFor="geography-select"
                className="!mb-0"
              >
                <Select
                  id="geography-select"
                  aria-label="Geography"
                  className="w-full"
                  mode="multiple"
                  placeholder="Select geographies"
                  value={formState.geographies}
                  onChange={(value) =>
                    setFormState((prev) => ({
                      ...prev,
                      geographies: value,
                      selectedDataUses: [],
                    }))
                  }
                  options={GEOGRAPHY_OPTIONS}
                  allowClear
                />
              </Form.Item>
            </Col>
          </Row>

          <DataUseCardsSection
            industry={formState.industry}
            dataUses={data?.items ?? []}
            isLoading={isLoading || isFetching}
            selectedDataUses={formState.selectedDataUses}
            onToggleDataUse={handleToggleDataUse}
          />

          <PrivacyPolicySection
            policyUrl={formState.policyUrl}
            onUrlChange={(url) =>
              setFormState((prev) => ({ ...prev, policyUrl: url }))
            }
          />
        </Flex>
      </Form>
    </div>
  );
};

export default OnboardingForm;
