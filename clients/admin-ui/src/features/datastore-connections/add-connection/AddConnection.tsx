import { Box, Heading, Text } from "@fidesui/react";
import { useAppSelector } from "app/hooks";
import {
  selectConnectionTypeState,
  setConnectionOption,
  setStep,
} from "connection-type/connection-type.slice";
import ConnectionTypeLogo from "datastore-connections/ConnectionTypeLogo";
import { useRouter } from "next/router";
import React, { useCallback, useEffect } from "react";
import { useDispatch } from "react-redux";

import ChooseConnection from "./ChooseConnection";
import ConfigureConnector from "./ConfigureConnector";
import { STEPS } from "./constants";
import { AddConnectionStep } from "./types";

const AddConnection: React.FC = () => {
  const dispatch = useDispatch();
  const router = useRouter();
  const { connectorType, step: currentStep } = router.query;

  const { connectionOption, step } = useAppSelector(selectConnectionTypeState);

  useEffect(() => {
    if (connectorType) {
      dispatch(setConnectionOption(JSON.parse(connectorType as string)));
    }
    if (router.query.step) {
      const item = STEPS.find((s) => s.stepId === Number(currentStep));
      dispatch(setStep(item || STEPS[1]));
    }
    return () => {};
  }, [connectorType, currentStep, dispatch, router.query.step]);

  const getLabel = useCallback(
    (s: AddConnectionStep): string => {
      let value: string = "";
      switch (s.stepId) {
        case 2:
        case 3:
          value = s.label.replace(
            "{identifier}",
            connectionOption!.human_readable
          );
          break;
        default:
          value = s.label;
          break;
      }
      return value;
    },
    [connectionOption]
  );

  return (
    <>
      <Heading
        fontSize="2xl"
        fontWeight="semibold"
        maxHeight="40px"
        mb="4px"
        whiteSpace="nowrap"
      >
        <Box alignItems="center" display="flex">
          {connectionOption && (
            <>
              <ConnectionTypeLogo data={connectionOption.identifier} />
              <Text ml="8px">{getLabel(step)}</Text>
            </>
          )}
          {!connectionOption && <Text>{getLabel(step)}</Text>}
        </Box>
      </Heading>
      {(() => {
        switch (step.stepId) {
          case 1:
            return <ChooseConnection />;
          case 2:
          case 3:
            return <ConfigureConnector />;
          default:
            return <ChooseConnection />;
        }
      })()}
    </>
  );
};

export default AddConnection;
