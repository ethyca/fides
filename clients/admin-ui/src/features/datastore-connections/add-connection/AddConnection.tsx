import {
  selectConnectionTypeState,
  setConnectionOption,
  setStep,
} from "connection-type/connection-type.slice";
import ConnectionTypeLogo from "datastore-connections/ConnectionTypeLogo";
import { AntSpace as Space, AntTypography as Typography } from "fidesui";
import { useRouter } from "next/router";
import React, { useCallback, useEffect } from "react";
import { useDispatch } from "react-redux";

import { useAppSelector } from "~/app/hooks";
import { DATASTORE_CONNECTION_ROUTE } from "~/features/common/nav/v2/routes";
import PageHeader from "~/features/common/PageHeader";

import ChooseConnection from "./ChooseConnection";
import ConfigureConnector from "./ConfigureConnector";
import { STEPS } from "./constants";
import { replaceURL } from "./helpers";
import { AddConnectionStep } from "./types";

const { Title } = Typography;

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
      <PageHeader
        heading="Connections"
        breadcrumbItems={[
          { title: "Unlinked connections", href: DATASTORE_CONNECTION_ROUTE },
          { title: "New connection" },
        ]}
      >
        <Title level={3} style={{ marginBottom: 0 }} className="mt-4">
          {connectionOption ? (
            <Space>
              <ConnectionTypeLogo data={connectionOption} />
              {getLabel(step)}
            </Space>
          ) : (
            getLabel(step)
          )}
        </Title>
      </PageHeader>
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
