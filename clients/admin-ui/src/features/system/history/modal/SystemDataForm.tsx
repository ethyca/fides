import { Stack } from "fidesui";
import { Form, Formik } from "formik";
import React, { Fragment } from "react";

import { useFeatures } from "~/features/common/features/features.slice";
import { PrivacyDeclaration, ResourceTypes } from "~/types/api";

import SystemCustomFieldGroup from "./fields/SystemCustomFieldGroup";
import SystemDataSwitch from "./fields/SystemDataSwitch";
import SystemDataTags from "./fields/SystemDataTags";
import SystemDataTextField from "./fields/SystemDataTextField";
import SystemDataGroup from "./SystemDataGroup";

interface SystemDataFormProps {
  initialValues: Record<string, any>;
}

const SystemDataForm = ({ initialValues }: SystemDataFormProps) => {
  const features = useFeatures();
  return (
    <Formik
      enableReinitialize
      initialValues={initialValues}
      onSubmit={() => {}}
    >
      {() => (
        <Form>
          <Stack>
            {/* System information */}
            <SystemDataGroup heading="System details">
              {features.dictionaryService ? (
                <SystemDataTextField
                  name="vendor_id"
                  label="Vendor"
                  tooltip="Select the vendor that matches the system"
                />
              ) : null}
              <SystemDataTextField
                name="name"
                label="System name"
                tooltip="Give the system a unique, and relevant name for reporting purposes. e.g. “Email Data Warehouse”"
              />
              <SystemDataTextField
                name="fides_key"
                label="Unique ID"
                disabled
                tooltip="An auto-generated unique ID based on the system name"
              />
              <SystemDataTextField
                name="description"
                label="Description"
                tooltip="Give the system a unique, and relevant name for reporting purposes. e.g. “Email Data Warehouse”"
              />
              <SystemDataTags
                name="tags"
                label="System Tags"
                tooltip="Are there any tags to associate with this system?"
              />
            </SystemDataGroup>
            <SystemDataGroup heading="Dataset reference">
              <SystemDataTags
                name="dataset_references"
                label="Dataset references"
                tooltip="Is there a dataset configured for this system"
              />
            </SystemDataGroup>
            <SystemDataGroup heading="Data processing properties">
              <SystemDataSwitch
                name="processes_personal_data"
                label="This system processes personal data"
                tooltip="Does this system process personal data?"
              />
              <SystemDataSwitch
                name="exempt_from_privacy_regulations"
                label="This system is exempt from privacy regulations"
                tooltip="Is this system exempt from privacy regulations?"
              />
              <SystemDataTextField
                name="reason_for_exemption"
                label="Reason for exemption"
                tooltip="Why is this system exempt from privacy regulation?"
              />
              <SystemDataSwitch
                name="uses_profiling"
                label="This system performs profiling"
                tooltip="Does this system perform profiling that could have a legal effect?"
              />
              <SystemDataTags
                name="legal_basis_for_profiling"
                label="Legal basis for profiling"
                tooltip="What is the legal basis under which profiling is performed?"
              />
              <SystemDataSwitch
                name="does_international_transfers"
                label="This system transfers data"
                tooltip="Does this system transfer data to other countries or international organizations?"
              />
              <SystemDataTags
                name="legal_basis_for_transfers"
                label="Legal basis for transfer"
                tooltip="What is the legal basis under which the data is transferred?"
              />
              <SystemDataSwitch
                name="requires_data_protection_assessments"
                label="This system requires Data Privacy Assessments"
                tooltip="Does this system require (DPA/DPIA) assessments?"
              />
              <SystemDataTextField
                label="DPIA/DPA location"
                name="dpa_location"
                tooltip="Where is the DPA/DPIA stored?"
              />
            </SystemDataGroup>
            <SystemDataGroup heading="Administrative properties">
              <SystemDataTextField
                label="Data stewards"
                name="data_stewards"
                tooltip="Who are the stewards assigned to the system?"
              />
              <SystemDataTextField
                name="privacy_policy"
                label="Privacy policy URL"
                tooltip="Where can the privacy
                policy be located?"
              />
              <SystemDataTextField
                name="legal_name"
                label="Legal name"
                tooltip="What is the legal name of the business?"
              />
              <SystemDataTextField
                name="legal_address"
                label="Legal address"
                tooltip="What is the legal address for the business?"
              />
              <SystemDataTextField
                label="Department"
                name="administrating_department"
                tooltip="Which department is concerned with this system?"
              />
              <SystemDataTags
                label="Responsibility"
                name="responsibility"
                tooltip="What is the role of the business with regard to data processing?"
              />
              <SystemDataTextField
                name="dpo"
                label="Legal contact (DPO)"
                tooltip="What is the official privacy contact information?"
              />
              <SystemDataTextField
                label="Joint controller"
                name="joint_controller_info"
                tooltip="Who are the party or parties that share responsibility for processing data?"
              />
              <SystemDataTextField
                label="Data security practices"
                name="data_security_practices"
                tooltip="Which data security practices are employed to keep the data safe?"
              />
            </SystemDataGroup>
            <SystemCustomFieldGroup
              customFields={initialValues.custom_fields}
              resourceType={ResourceTypes.SYSTEM}
            />
            {/* Data uses */}
            {initialValues.privacy_declarations &&
              initialValues.privacy_declarations.map(
                (_: PrivacyDeclaration, index: number) => (
                  // eslint-disable-next-line react/no-array-index-key
                  <Fragment key={index}>
                    <SystemDataGroup heading="Data use">
                      <SystemDataTextField
                        label="Declaration name (optional)"
                        name={`privacy_declarations[${index}].name`}
                        tooltip="Would you like to append anything to the system name?"
                      />
                      <SystemDataTextField
                        name={`privacy_declarations[${index}].data_use`}
                        label="Data use"
                        tooltip="For which business purposes is this data used?"
                      />
                      <SystemDataTags
                        name={`privacy_declarations[${index}].data_categories`}
                        label="Data categories"
                        tooltip="Which categories of personal data are collected for this purpose?"
                      />
                      <SystemDataTags
                        name={`privacy_declarations[${index}].data_subjects`}
                        label="Data subjects"
                        tooltip="Who are the subjects for this personal data?"
                      />
                      <SystemDataTextField
                        name={`privacy_declarations[${index}].legal_basis_for_processing`}
                        label="Legal basis for processing"
                        tooltip="What is the legal basis under which personal data is processed for this purpose?"
                      />
                      <SystemDataTextField
                        name={`privacy_declarations[${index}].impact_assessment_location`}
                        label="Impact assessment location"
                        tooltip="Where is the legitimate interest impact assessment stored?"
                      />
                      <SystemDataTextField
                        name={`privacy_declarations[${index}].retention_period`}
                        label="Retention period (days)"
                        tooltip="How long is personal data retained for this purpose?"
                      />
                    </SystemDataGroup>
                    <SystemDataGroup heading="Features">
                      <SystemDataTags
                        name={`privacy_declarations[${index}].features`}
                        label="Features"
                        tooltip="What are some features of how data is processed?"
                      />
                    </SystemDataGroup>
                    <SystemDataGroup heading="Dataset reference">
                      <SystemDataTags
                        name={`privacy_declarations[${index}].dataset_references`}
                        label="Dataset references"
                        tooltip="Is there a dataset configured for this system?"
                      />
                    </SystemDataGroup>
                    <SystemDataGroup heading="Special category data">
                      <SystemDataSwitch
                        name={`privacy_declarations[${index}].processes_special_category_data`}
                        label="This system processes special category data"
                        tooltip="Is this system processing special category data as defined by GDPR Article 9?"
                      />
                      <SystemDataTextField
                        name={`privacy_declarations[${index}].special_category_legal_basis`}
                        label="Legal basis for processing"
                        tooltip="What is the legal basis under which the special category data is processed?"
                      />
                    </SystemDataGroup>
                    <SystemDataGroup heading="Third parties">
                      <SystemDataSwitch
                        name={`privacy_declarations[${index}].data_shared_with_third_parties`}
                        label="This system shares data with 3rd parties for this purpose"
                        tooltip="Does this system disclose, sell, or share personal data collected for this business use with 3rd parties?"
                      />
                      <SystemDataTextField
                        name={`privacy_declarations[${index}].third_parties`}
                        label="Third parties"
                        tooltip="Which type of third parties is the data shared with?"
                      />
                      <SystemDataTags
                        name={`privacy_declarations[${index}].shared_categories`}
                        label="Shared categories"
                        tooltip="Which categories of personal data does this system share with third parties?"
                      />
                    </SystemDataGroup>
                    <SystemCustomFieldGroup
                      customFields={
                        initialValues.privacy_declarations[0].custom_fields
                      }
                      resourceType={ResourceTypes.PRIVACY_DECLARATION}
                    />
                  </Fragment>
                ),
              )}
            {/* System flow */}
            <SystemDataGroup heading="Data flow">
              <SystemDataTags name="ingress" label="Sources" />
              <SystemDataTags name="egress" label="Destinations" />
            </SystemDataGroup>
          </Stack>
        </Form>
      )}
    </Formik>
  );
};

export default SystemDataForm;
