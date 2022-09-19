/* eslint-disable no-param-reassign */
import { VStack } from "@fidesui/react";
import { useAppSelector } from "app/hooks";
import { selectConnectionTypeState } from "connection-type/connection-type.slice";
import { Form, Formik } from "formik";
import { useRouter } from "next/router";
import { DATASTORE_CONNECTION_ROUTE } from "src/constants";
import * as Yup from "yup";

import CustomInput from "../forms/CustomInput";
import { BaseConnectorParametersFields } from "../types";
import { ButtonGroup as ManualButtonGroup } from "./ButtonGroup";

type ConnectorParametersFormProps = {
  defaultValues: BaseConnectorParametersFields;
  isSubmitting: boolean;
  onSaveClick: (values: any, actions: any) => void;
};

const ConnectorParametersForm: React.FC<ConnectorParametersFormProps> = ({
  defaultValues,
  isSubmitting = false,
  onSaveClick,
}) => {
  const router = useRouter();

  const { connection, connectionOption } = useAppSelector(
    selectConnectionTypeState
  );
  const getInitialValues = () => {
    if (connection?.key) {
      defaultValues.name = connection.name;
      defaultValues.description = connection.description as string;
    }
    return defaultValues;
  };

  const handleCancel = () => {
    router.push(DATASTORE_CONNECTION_ROUTE);
  };

  const handleSubmit = (values: any, actions: any) => {
    onSaveClick(values, actions);
  };

  return (
    <Formik
      initialValues={getInitialValues()}
      onSubmit={handleSubmit}
      validateOnBlur={false}
      validateOnChange={false}
      validationSchema={Yup.object().shape({
        name: Yup.string().required("Name is required"),
      })}
    >
      <Form noValidate>
        <VStack align="stretch" gap="24px">
          {/* Name */}
          <CustomInput
            autoFocus
            disabled={!!connection?.key}
            isRequired
            label="Name"
            name="name"
            placeholder={`Enter a friendly name for your new ${
              connectionOption!.human_readable
            } connection`}
          />
          {/* Description */}
          <CustomInput
            label="Description"
            name="description"
            placeholder={`Enter a description for your new ${
              connectionOption!.human_readable
            } connection`}
            type="textarea"
          />
          <ManualButtonGroup
            isSubmitting={isSubmitting}
            onCancelClick={handleCancel}
          />
        </VStack>
      </Form>
    </Formik>
  );
};

export default ConnectorParametersForm;
