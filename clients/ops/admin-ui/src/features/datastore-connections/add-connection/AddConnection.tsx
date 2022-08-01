import {
  Box,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  Heading,
} from "@fidesui/react";
import { useRouter } from "next/router";
import React, { useCallback, useEffect, useState } from "react";

import ChooseConnection from "./ChooseConnection";
import { STEPS } from "./constants";

const AddConnection: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(STEPS[1]);
  const router = useRouter();

  useEffect(() => {
    if (router.query.step) {
      const item = STEPS.find((s) => s.stepId === Number(router.query.step));
      setCurrentStep(item || STEPS[1]);
    }
  }, [router.query.step]);

  const getComponent = useCallback(() => {
    switch (currentStep.stepId) {
      case 1:
        return <ChooseConnection currentStep={currentStep} />;
      default:
        return <ChooseConnection currentStep={currentStep} />;
    }
  }, [currentStep]);

  return (
    <>
      <Heading fontSize="2xl" fontWeight="semibold" maxHeight="52px" mb="16px">
        {currentStep.label}
        <Box mt={2} mb={7}>
          <Breadcrumb fontSize="sm" fontWeight="medium">
            {STEPS.slice(0, currentStep.stepId + 1).map((step) => (
              <BreadcrumbItem key={step.stepId}>
                <BreadcrumbLink href={step.href}>{step.label}</BreadcrumbLink>
              </BreadcrumbItem>
            ))}
          </Breadcrumb>
        </Box>
      </Heading>
      {getComponent()}
    </>
  );
};

export default AddConnection;
