import {
  selectConnectionTypeState,
  setConnectionOption,
  setStep,
} from "connection-type/connection-type.slice";
import ConnectionTypeLogo from "datastore-connections/ConnectionTypeLogo";
import { Box, Heading, Text } from "fidesui";
import { useRouter } from "next/router";
import React, { useCallback, useEffect } from "react";
import { useDispatch } from "react-redux";

import { useAppSelector } from "~/app/hooks";
import BackButton from "~/features/common/nav/v2/BackButton";
import { DATASTORE_CONNECTION_ROUTE } from "~/features/common/nav/v2/routes";

import ChooseConnection from "./ChooseConnection";
import ConfigureConnector from "./ConfigureConnector";
import { STEPS } from "./constants";
import { replaceURL } from "./helpers";
import { AddConnectionStep } from "./types";

const AddConnection = () => {
  const dispatch = useDispatch();
  const router = useRouter();
  const { connectorType, step: currentStep } = router.query;

  const { connection, connectionOption, step } = useAppSelector(
    selectConnectionTypeState,
  );

  useEffect(() => {
    if (connectorType) {
      dispatch(setConnectionOption(JSON.parse(connectorType as string)));
    }
    if (router.query.step) {
      const item = STEPS.find((s) => s.stepId === Number(currentStep));
      dispatch(setStep(item || STEPS[1]));
    }
    if (!router.query.id && connection?.key) {
      replaceURL(connection.key, step.href);
    }
    return () => {};
  }, [
    connection?.key,
    connectorType,
    currentStep,
    dispatch,
    router.query.id,
    router.query.step,
    step.href,
  ]);

  const getLabel = useCallback(
    (s: AddConnectionStep): string => {
      let value: string = "";
      switch (s.stepId) {
        case 2:
        case 3:
          value = s.label.replace(
            "{identifier}",
            connectionOption!.human_readable,
          );
          break;
        default:
          value = s.label;
          break;
      }
      return value;
    },
    [connectionOption],
  );

  return (
    <>
      <BackButton backPath={DATASTORE_CONNECTION_ROUTE} />
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
              <ConnectionTypeLogo data={connectionOption} />
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
