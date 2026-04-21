import {
  Button,
  ExpandCollapse,
  Flex,
  Form,
  Icons,
  Input,
  Select,
  Switch,
  Typography,
} from "fidesui";
import { isEqual } from "lodash";
import { useEffect, useMemo, useState } from "react";

import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import ConfirmCloseModal from "~/features/common/modals/ConfirmCloseModal";
import useLegalBasisOptions from "~/features/system/system-form-declaration-tab/useLegalBasisOptions";
import useSpecialCategoryLegalBasisOptions from "~/features/system/system-form-declaration-tab/useSpecialCategoryLegalBasisOptions";
import { PrivacyDeclarationResponse } from "~/types/api";

import styles from "./EditMinimalDataUseModal.module.scss";

interface EditMinimalDataUseProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (values: PrivacyDeclarationResponse) => void;
  declaration: PrivacyDeclarationResponse;
}

const EditMinimalDataUseModal = ({
  isOpen,
  onClose,
  onSave,
  declaration,
}: EditMinimalDataUseProps) => {
  const { getDataUses, getDataCategories, getDataSubjects } = useTaxonomies();

  const [isAdvancedSettingsOpen, setIsAdvancedSettingsOpen] = useState(false);

  const [form] = Form.useForm<PrivacyDeclarationResponse>();
  const allValues = Form.useWatch([], form);

  const [submittable, setSubmittable] = useState(false);

  useEffect(() => {
    form
      .validateFields({ validateOnly: true })
      .then(() => setSubmittable(true))
      .catch(() => setSubmittable(false));
  }, [form, allValues]);

  const isDirty = useMemo(
    () => !isEqual(form.getFieldsValue(true), declaration),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [allValues, declaration],
  );

  const handleFinish = (values: PrivacyDeclarationResponse) => {
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

  const legalBasisForProcessing = Form.useWatch(
    "legal_basis_for_processing",
    form,
  );
  const processesSpecialCategoryData = Form.useWatch(
    "processes_special_category_data",
    form,
  );

  return (
    <ConfirmCloseModal
      title="Edit data use"
      open={isOpen}
      onClose={onClose}
      getIsDirty={() => isDirty}
      centered
      destroyOnHidden
      footer={null}
    >
      <Form
        form={form}
        initialValues={declaration}
        onFinish={handleFinish}
        layout="vertical"
        key={declaration?.id ?? "edit"}
      >
        <Flex vertical className="gap-6 py-4">
          <Form.Item
            name="data_use"
            label="Data use"
            rules={[{ required: true, message: "Data use is required" }]}
          >
            <Select options={dataUseOptions} aria-label="Data use" />
          </Form.Item>
          <Form.Item name="data_categories" label="Data categories">
            <Select
              options={dataCategoryOptions}
              mode="multiple"
              aria-label="Data categories"
            />
          </Form.Item>
          <Form.Item name="data_subjects" label="Data subjects">
            <Select
              options={dataSubjectOptions}
              mode="multiple"
              aria-label="Data subjects"
            />
          </Form.Item>
          <Form.Item name="name" label="Declaration name">
            <Input />
          </Form.Item>
          <Flex
            vertical
            // eslint-disable-next-line tailwindcss/no-custom-classname
            className={`gap-6 p-4 ${styles.advancedSettings}`}
          >
            <Flex
              className="cursor-pointer justify-between"
              onClick={() => setIsAdvancedSettingsOpen((prev) => !prev)}
            >
              <Typography.Text className="text-xs">
                Advanced settings
              </Typography.Text>
              <Icons.ChevronDown
                className={isAdvancedSettingsOpen ? "rotate-180" : undefined}
              />
            </Flex>
            <ExpandCollapse isExpanded={isAdvancedSettingsOpen}>
              <Flex vertical className="gap-4">
                <Form.Item
                  name="legal_basis_for_processing"
                  label="Legal basis for processing"
                >
                  <Select
                    options={legalBasisOptions}
                    aria-label="Legal basis for processing"
                  />
                </Form.Item>
                <ExpandCollapse
                  isExpanded={
                    legalBasisForProcessing === "Legitimate interests"
                  }
                  motionKey="impact-assessment"
                >
                  <div className="mt-4">
                    <Form.Item
                      name="impact_assessment_location"
                      label="Impact assessment location"
                      tooltip="Where is the legitimate interest impact assessment stored?"
                    >
                      <Input />
                    </Form.Item>
                  </div>
                </ExpandCollapse>
                <Form.Item
                  name="flexible_legal_basis_for_processing"
                  label="This legal basis is flexible"
                  tooltip="Has the vendor declared that the legal basis may be overridden?"
                  layout="horizontal"
                  colon={false}
                  valuePropName="checked"
                >
                  <Switch size="small" />
                </Form.Item>
                <Form.Item
                  name="retention_period"
                  label="Retention period (days)"
                  tooltip="How long is personal data retained for this purpose?"
                >
                  <Input />
                </Form.Item>

                <Flex vertical>
                  <Form.Item
                    name="processes_special_category_data"
                    label="This system processes special category data"
                    tooltip="Is this system processing special category data as defined by GDPR Article 9?"
                    layout="horizontal"
                    colon={false}
                    valuePropName="checked"
                  >
                    <Switch size="small" />
                  </Form.Item>
                  <ExpandCollapse
                    isExpanded={!!processesSpecialCategoryData}
                    motionKey="special-category"
                  >
                    <div className="mt-4">
                      <Form.Item
                        name="special_category_legal_basis"
                        label="Legal basis for processing"
                        tooltip="What is the legal basis under which the special category data is processed?"
                        rules={[
                          {
                            required: !!processesSpecialCategoryData,
                            message:
                              "Legal basis for processing is required when processing special category data",
                          },
                        ]}
                      >
                        <Select
                          options={specialCategoryLegalBasisOptions}
                          aria-label="Special category legal basis"
                        />
                      </Form.Item>
                    </div>
                  </ExpandCollapse>
                </Flex>
              </Flex>
            </ExpandCollapse>
          </Flex>
        </Flex>
        <div className="flex w-full justify-between">
          <Button
            onClick={() => {
              form.resetFields();
              onClose();
            }}
          >
            Cancel
          </Button>
          <Button
            type="primary"
            htmlType="submit"
            disabled={!isDirty || !submittable}
            data-testid="save-btn"
          >
            Save
          </Button>
        </div>
      </Form>
    </ConfirmCloseModal>
  );
};

export default EditMinimalDataUseModal;
