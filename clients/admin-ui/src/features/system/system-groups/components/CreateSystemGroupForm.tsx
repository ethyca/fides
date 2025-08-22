import { AntButton as Button, AntFlex as Flex } from "fidesui";
import { CustomTypography } from "fidesui/src/hoc/CustomTypography";
import { Form, Formik } from "formik";
import { useMemo } from "react";
import * as Yup from "yup";

import { ControlledSelect } from "~/features/common/form/ControlledSelect";
import { CustomTextArea, CustomTextInput } from "~/features/common/form/inputs";
import { useGetAllDataUsesQuery } from "~/features/data-use/data-use.slice";
import { useGetAllSystemsQuery } from "~/features/system";
import ColorSelect from "~/features/system/system-groups/components/ColorSelect";
import { useGetAllUsersQuery } from "~/features/user-management/user-management.slice";
import {
  CustomTaxonomyColor,
  DataUse,
  SystemGroupCreate,
  SystemResponse,
} from "~/types/api";

interface CreateSystemGroupFormProps {
  selectedSystems?: string[];
  onSubmit: (values: SystemGroupCreate) => void;
  onCancel: () => void;
  isSubmitting?: boolean;
}

const validationSchema = Yup.object().shape({
  name: Yup.string().required("Name is required").label("Name"),
  label_color: Yup.string().required("Color is required").label("Color"),
  systems: Yup.array().of(Yup.string()).label("Systems"),
  data_uses: Yup.array().of(Yup.string()).label("Data uses"),
});

const CreateSystemGroupForm = ({
  selectedSystems = [],
  onSubmit,
  onCancel,
  isSubmitting = false,
}: CreateSystemGroupFormProps) => {
  const { data: dataUses = [], isLoading: isLoadingDataUses } =
    useGetAllDataUsesQuery();

  const { data: usersResponse, isLoading: isLoadingUsers } =
    useGetAllUsersQuery({
      page: 1,
      size: 100,
      username: "",
    });

  const { data: allSystems, isLoading: isLoadingSystems } =
    useGetAllSystemsQuery();

  const users = usersResponse?.items ?? [];

  const dataUseOptions = useMemo(
    () =>
      dataUses.map((dataUse: DataUse) => ({
        label: dataUse.name || dataUse.fides_key,
        value: dataUse.fides_key,
      })),
    [dataUses],
  );

  const userOptions = users.map((user) => ({
    label:
      `${user.first_name || ""} ${user.last_name || ""} (${user.email_address || user.username})`.trim(),
    value: user.id,
  }));

  const systemOptions = useMemo(
    () =>
      allSystems?.map((system: SystemResponse) => ({
        label: system.name || system.fides_key,
        value: system.fides_key,
      })) ?? [],
    [allSystems],
  );

  const initialValues: SystemGroupCreate = {
    name: "",
    description: "",
    label_color: CustomTaxonomyColor.TAXONOMY_WHITE,
    systems: selectedSystems,
    data_uses: [],
    active: true,
  };

  return (
    <Formik
      initialValues={initialValues}
      validationSchema={validationSchema}
      onSubmit={onSubmit}
      enableReinitialize
    >
      {({ isValid, dirty }) => {
        return (
          <Form>
            <Flex vertical gap="middle">
              <CustomTypography.Title level={2}>
                Create system group
              </CustomTypography.Title>
              <CustomTextInput
                name="name"
                label="Name"
                isRequired
                variant="stacked"
                placeholder="Enter system group name"
              />

              <CustomTextArea
                name="description"
                label="Description"
                variant="stacked"
                placeholder="Enter system group description"
                resize={false}
              />

              <ControlledSelect
                name="systems"
                label="Systems"
                mode="multiple"
                placeholder="Select systems"
                options={systemOptions}
                layout="stacked"
                allowClear
                loading={isLoadingSystems}
              />

              <ColorSelect name="label_color" label="Color" />

              <ControlledSelect
                name="data_uses"
                label="Data Uses"
                mode="multiple"
                placeholder="Select data uses"
                options={dataUseOptions}
                layout="stacked"
                allowClear
                loading={isLoadingDataUses}
              />

              <ControlledSelect
                name="data_steward"
                label="Data Steward"
                placeholder="Select a data steward"
                options={userOptions}
                layout="stacked"
                allowClear
                loading={isLoadingUsers}
              />

              <Flex gap="small" justify="space-between" className="pt-4">
                <Button onClick={onCancel} disabled={isSubmitting}>
                  Cancel
                </Button>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={isSubmitting}
                  disabled={!isValid || !dirty || isSubmitting}
                >
                  Create group
                </Button>
              </Flex>
            </Flex>
          </Form>
        );
      }}
    </Formik>
  );
};

export default CreateSystemGroupForm;
