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
  const { connectorType, key, step: currentStep } = router.query;

  const { connectionOption, step } = useAppSelector(selectConnectionTypeState);

  /**
   * NOTE: If the user reloads the web page via F5, the react redux store state is lost.
   * By default its persisted in internal memory. As a result, a runtime exception occurs
   * which impedes the page rendering.
   *
   * @example
   * The above error occurred in the <AddConnection> component
   *
   * For now, a temporary solution is to redirect the user
   * to the "Choose your connection" step. This allows a better overall user experience.
   * A permanent solution will be to persist the react redux store state to either local storage
   * or session storage. Once completed, this method can be deleted.
   */
  const reload = useCallback(() => {
    if (
      key &&
      currentStep &&
      (currentStep as unknown as number) !== step?.stepId
    ) {
      window.location.href = STEPS[1].href;
    }
  }, [currentStep, key, step?.stepId]);

  useEffect(() => {
    reload();
    if (connectorType) {
      dispatch(setConnectionOption(JSON.parse(connectorType as string)));
    }
    if (router.query.step) {
      const item = STEPS.find((s) => s.stepId === Number(currentStep));
      dispatch(setStep(item || STEPS[1]));
    }
    return () => {};
  }, [connectorType, currentStep, dispatch, reload, router.query.step]);

  const getComponent = useCallback(() => {
    switch (step.stepId) {
      case 1:
        return <ChooseConnection />;
      case 2:
      case 3:
        return <ConfigureConnector />;
      default:
        return <ChooseConnection />;
    }
  }, [step.stepId]);

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
      {getComponent()}
    </>
  );
};

export default AddConnection;
