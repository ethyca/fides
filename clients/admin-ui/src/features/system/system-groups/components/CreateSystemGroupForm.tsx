import { AntButton as Button, AntFlex as Flex } from "fidesui";
import { CustomTypography } from "fidesui/src/hoc/CustomTypography";
import { Form, Formik } from "formik";
import { uniq } from "lodash";
import { useMemo } from "react";
import * as Yup from "yup";

import { ControlledSelect } from "~/features/common/form/ControlledSelect";
import { CustomTextArea, CustomTextInput } from "~/features/common/form/inputs";
import { useGetAllDataUsesQuery } from "~/features/data-use/data-use.slice";
import { useGetAllSystemsQuery } from "~/features/system";
import ColorSelect from "~/features/system/system-groups/components/ColorSelect";
import DataUseSelectWithSuggestions from "~/features/system/system-groups/components/DataUseSelectWithSuggestions";
import {
  CustomTaxonomyColor,
  DataUse,
  SystemGroupCreate,
  SystemResponse,
} from "~/types/api";

interface CreateSystemGroupFormProps {
  selectedSystemKeys?: string[];
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
  selectedSystemKeys = [],
  onSubmit,
  onCancel,
  isSubmitting = false,
}: CreateSystemGroupFormProps) => {
  const { data: dataUses = [], isLoading: isLoadingDataUses } =
    useGetAllDataUsesQuery();

  const { data: allSystems, isLoading: isLoadingSystems } =
    useGetAllSystemsQuery();

  const dataUseOptions = useMemo(
    () =>
      dataUses.map((dataUse: DataUse) => ({
        label: dataUse.name || dataUse.fides_key,
        value: dataUse.fides_key,
      })),
    [dataUses],
  );

  const suggestedDataUses: string[] = useMemo(() => {
    const selectedSystems: SystemResponse[] =
      allSystems?.filter((system) =>
        selectedSystemKeys.includes(system.fides_key),
      ) ?? [];
    return uniq(
      selectedSystems?.flatMap((system) =>
        system.privacy_declarations.map((d) => d.data_use),
      ),
    );
  }, [allSystems, selectedSystemKeys]);

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
    systems: selectedSystemKeys,
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

              <DataUseSelectWithSuggestions
                name="data_uses"
                options={dataUseOptions}
                loading={isLoadingDataUses}
                suggestedDataUses={suggestedDataUses}
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
