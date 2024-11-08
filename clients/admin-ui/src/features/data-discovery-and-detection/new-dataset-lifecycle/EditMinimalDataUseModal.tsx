import { AntButton as Button, Box, Collapse, Flex, Stack } from "fidesui";
import { Form, Formik } from "formik";
import * as Yup from "yup";

import AdvancedSettings from "~/features/common/form/AdvancedSettings";
import {
  CustomSelect,
  CustomSwitch,
  CustomTextInput,
} from "~/features/common/form/inputs";
import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import FormModal from "~/features/common/modals/FormModal";
import useLegalBasisOptions from "~/features/system/system-form-declaration-tab/useLegalBasisOptions";
import useSpecialCategoryLegalBasisOptions from "~/features/system/system-form-declaration-tab/useSpecialCategoryLegalBasisOptions";
import { PrivacyDeclarationResponse } from "~/types/api";

interface EditMinimalDataUseProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (values: PrivacyDeclarationResponse) => void;
  declaration: PrivacyDeclarationResponse;
}

const validationSchema = Yup.object().shape({
  data_use: Yup.string().required("Data use is required"),
});

const EditMinimalDataUseModal = ({
  isOpen,
  onClose,
  onSave,
  declaration,
}: EditMinimalDataUseProps) => {
  const { getDataUses, getDataCategories, getDataSubjects } = useTaxonomies();

  const handleSubmit = (values: PrivacyDeclarationResponse) => {
    onSave(values);
    onClose();
  };

  const dataUseOptions = getDataUses().map((use) => ({
    label: use.fides_key,
    value: use.fides_key,
  }));

  const dataCategoryOptions = getDataCategories().map((category) => ({
    label: category.fides_key,
    value: category.fides_key,
  }));

  const dataSubjectOptions = getDataSubjects().map((subject) => ({
    label: subject.fides_key,
    value: subject.fides_key,
  }));

  const { legalBasisOptions } = useLegalBasisOptions();
  const { specialCategoryLegalBasisOptions } =
    useSpecialCategoryLegalBasisOptions();

  return (
    <Formik
      initialValues={declaration}
      enableReinitialize
      onSubmit={handleSubmit}
      validationSchema={validationSchema}
    >
      {({ dirty, isValid, values, resetForm }) => (
        <FormModal title="Edit data use" isOpen={isOpen} onClose={onClose}>
          <Form>
            <Flex py={4} gap={6} direction="column">
              <CustomSelect
                name="data_use"
                label="Data use"
                options={dataUseOptions}
                variant="stacked"
                singleValueBlock
                isRequired
              />
              <CustomSelect
                name="data_categories"
                label="Data categories"
                options={dataCategoryOptions}
                variant="stacked"
                isMulti
              />
              <CustomSelect
                name="data_subjects"
                label="Data subjects"
                options={dataSubjectOptions}
                variant="stacked"
                isMulti
              />
              <CustomTextInput
                name="name"
                label="Declaration name"
                variant="stacked"
              />
              <AdvancedSettings>
                <CustomSelect
                  name="legal_basis_for_processing"
                  label="Legal basis for processing"
                  options={legalBasisOptions}
                  variant="stacked"
                />
                <Collapse
                  in={
                    values?.legal_basis_for_processing ===
                    "Legitimate interests"
                  }
                  animateOpacity
                  style={{ overflow: "visible" }}
                >
                  <Box mt={4}>
                    <CustomTextInput
                      name="impact_assessment_location"
                      label="Impact assessment location"
                      tooltip="Where is the legitimate interest impact assessment stored?"
                      variant="stacked"
                    />
                  </Box>
                </Collapse>
                <CustomSwitch
                  name="flexible_legal_basis_for_processing"
                  label="This legal basis is flexible"
                  tooltip="Has the vendor declared that the legal basis may be overridden?"
                  variant="stacked"
                />
                <CustomTextInput
                  name="retention_period"
                  label="Retention period (days)"
                  tooltip="How long is personal data retained for this purpose?"
                  variant="stacked"
                />

                <Stack spacing={0}>
                  <CustomSwitch
                    name="processes_special_category_data"
                    label="This system processes special category data"
                    tooltip="Is this system processing special category data as defined by GDPR Article 9?"
                    variant="stacked"
                  />
                  <Collapse
                    in={values?.processes_special_category_data}
                    animateOpacity
                    style={{ overflow: "visible" }}
                  >
                    <Box mt={4}>
                      <CustomSelect
                        isRequired
                        name="special_category_legal_basis"
                        label="Legal basis for processing"
                        options={specialCategoryLegalBasisOptions}
                        tooltip="What is the legal basis under which the special category data is processed?"
                        variant="stacked"
                      />
                    </Box>
                  </Collapse>
                </Stack>
              </AdvancedSettings>
            </Flex>
            <div className="flex w-full justify-between">
              <Button
                onClick={() => {
                  resetForm();
                  onClose();
                }}
              >
                Cancel
              </Button>
              <Button
                type="primary"
                htmlType="submit"
                disabled={!dirty || !isValid}
                loading={false}
                data-testid="save-btn"
              >
                Save
              </Button>
            </div>
          </Form>
        </FormModal>
      )}
    </Formik>
  );
};

export default EditMinimalDataUseModal;
