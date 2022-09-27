import {
  Box,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  Heading,
  Text,
} from "@fidesui/react";
import { capitalize } from "common/utils";
import { ConnectionOption } from "connection-type/types";
import ConnectionTypeLogo from "datastore-connections/ConnectionTypeLogo";
import { useRouter } from "next/router";
import React, { useCallback, useEffect, useState } from "react";

import ChooseConnection from "./ChooseConnection";
import ConfigureConnector from "./ConfigureConnector";
import { STEPS } from "./constants";
import { AddConnectionStep } from "./types";

const AddConnection: React.FC = () => {
  const router = useRouter();

  const [currentStep, setCurrentStep] = useState(STEPS[1]);
  const [connectionOption, setConnectionOption] = useState(
    undefined as unknown as ConnectionOption
  );

  useEffect(() => {
    if (router.query.connectorType) {
      setConnectionOption(JSON.parse(router.query.connectorType as string));
    }
    if (router.query.step) {
      const item = STEPS.find((s) => s.stepId === Number(router.query.step));
      setCurrentStep(item || STEPS[1]);
    }
  }, [router.query.connectorType, router.query.step]);

  const getComponent = useCallback(() => {
    switch (currentStep.stepId) {
      case 1:
        return <ChooseConnection currentStep={currentStep} />;
      case 2:
        return (
          <ConfigureConnector
            currentStep={currentStep}
            connectionOption={connectionOption}
          />
        );
      default:
        return <ChooseConnection currentStep={currentStep} />;
    }
  }, [connectionOption, currentStep]);

  const getLabel = useCallback(
    (step: AddConnectionStep): string => {
      let value: string = "";
      switch (currentStep.stepId) {
        case 2:
          value = step.label.replace(
            "{identifier}",
            capitalize(connectionOption.identifier)
          );
          break;
        default:
          value = step.label;
          break;
      }
      return value;
    },
    [connectionOption?.identifier, currentStep.stepId]
  );

  return (
    <>
      <Heading
        fontSize="2xl"
        fontWeight="semibold"
        maxHeight="52px"
        mb="32px"
        whiteSpace="nowrap"
      >
        <Box alignItems="center" display="flex">
          {connectionOption && (
            <>
              <ConnectionTypeLogo data={connectionOption.identifier} />
              <Text ml="8px">{getLabel(currentStep)}</Text>
            </>
          )}
        </Box>
        <Box mt={2} mb={7}>
          <Breadcrumb fontSize="sm" fontWeight="medium">
            {STEPS.slice(0, currentStep.stepId + 1).map((step) => (
              <BreadcrumbItem key={step.stepId}>
                {step !== currentStep && (
                  <BreadcrumbLink href={step.href}>
                    {getLabel(step)}
                  </BreadcrumbLink>
                )}
                {step === currentStep && (
                  <BreadcrumbLink
                    isCurrentPage
                    color="complimentary.500"
                    _hover={{ textDecoration: "none" }}
                  >
                    {getLabel(step)}
                  </BreadcrumbLink>
                )}
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
