import React from "react";
import { Formik, Form } from "formik";
import SystemDataGroup from "./SystemDataGroup";
import SystemDataTextField from "./fields/SystemDataTextField";
import { Stack } from "@fidesui/react";
import { useFeatures } from "~/features/common/features/features.slice";
import SystemDataSwitch from "./fields/SystemDataSwitch";
import SystemDataTags from "./fields/SystemDataTags";

const SystemDataForm = ({ initialValues }) => {
  const features = useFeatures();
  return (
    <Formik initialValues={initialValues} enableReinitialize>
      {() => (
        <Form>
          <Stack>
            {/* System information */}
            <SystemDataGroup heading="System details">
              {features.dictionaryService ? (
                <SystemDataTextField
                  id="meta.vendor.id"
                  name="meta.vendor.id"
                  label="Vendor"
                  tooltip="Select the vendor that matches the system"
                  variant="stacked"
                />
              ) : null}
              <SystemDataTextField
                id="name"
                name="name"
                label="System name"
                variant="stacked"
                tooltip="Give the system a unique, and relevant name for reporting purposes. e.g. “Email Data Warehouse”"
              />
              <SystemDataTextField
                id="fides_key"
                name="fides_key"
                label="Unique ID"
                disabled
                variant="stacked"
                tooltip="An auto-generated unique ID based on the system name"
              />
              <SystemDataTextField
                id="description"
                name="description"
                label="Description"
                variant="stacked"
                tooltip="Give the system a unique, and relevant name for reporting purposes. e.g. “Email Data Warehouse”"
              />
              <SystemDataTags
                id="tags"
                name="tags"
                label="System Tags"
                variant="stacked"
                tooltip="Are there any tags to associate with this system?"
              />
            </SystemDataGroup>
            <SystemDataGroup heading="Dataset reference">
              <SystemDataTags
                id="dataset_references"
                name="dataset_references"
                label="Dataset references"
                variant="stacked"
                tooltip="Is there a dataset configured for this system"
              />
            </SystemDataGroup>
            <SystemDataGroup heading="Data processing properties">
              <SystemDataSwitch
                id="processes_personal_data"
                name="processes_personal_data"
                label="This system processes personal data"
                tooltip="Does this system process personal data?"
                variant="stacked"
              />
              <SystemDataSwitch
                name="exempt_from_privacy_regulations"
                label="This system is exempt from privacy regulations"
                tooltip="Is this system exempt from privacy regulations?"
                variant="stacked"
              />
              <SystemDataTextField
                name="reason_for_exemption"
                label="Reason for exemption"
                tooltip="Why is this system exempt from privacy regulation?"
                variant="stacked"
              />
              <SystemDataSwitch
                name="uses_profiling"
                dictField="uses_profiling"
                label="This system performs profiling"
                tooltip="Does this system perform profiling that could have a legal effect?"
              />
              <SystemDataTags
                name="legal_basis_for_profiling"
                dictField="legal_basis_for_profiling"
                label="Legal basis for profiling"
                tooltip="What is the legal basis under which profiling is performed?"
              />
              <SystemDataSwitch
                name="does_international_transfers"
                dictField="international_transfers"
                label="This system transfers data"
                tooltip="Does this system transfer data to other countries or international organizations?"
              />
              <SystemDataTags
                name="legal_basis_for_transfers"
                dictField="legal_basis_for_transfers"
                label="Legal basis for transfer"
                tooltip="What is the legal basis under which the data is transferred?"
              />
              <SystemDataSwitch
                name="requires_data_protection_assessments"
                label="This system requires Data Privacy Assessments"
                tooltip="Does this system require (DPA/DPIA) assessments?"
                variant="stacked"
              />
              <SystemDataTextField
                label="DPIA/DPA location"
                name="dpa_location"
                tooltip="Where is the DPA/DPIA stored?"
                variant="stacked"
              />
            </SystemDataGroup>
            <SystemDataGroup heading="Administrative properties">
              <SystemDataTextField
                label="Data stewards"
                name="data_stewards"
                tooltip="Who are the stewards assigned to the system?"
                variant="stacked"
              />
              <SystemDataTextField
                id="privacy_policy"
                name="privacy_policy"
                label="Privacy policy URL"
                dictField="privacy_policy"
                tooltip="Where can the privacy
                policy be located?"
              />
              <SystemDataTextField
                id="legal_name"
                name="legal_name"
                label="Legal name"
                tooltip="What is the legal name of the business?"
                variant="stacked"
              />
              <SystemDataTextField
                id="legal_address"
                name="legal_address"
                label="Legal address"
                tooltip="What is the legal address for the business?"
                dictField="legal_address"
              />
              <SystemDataTextField
                label="Department"
                name="administrating_department"
                tooltip="Which department is concerned with this system?"
                variant="stacked"
              />
              <SystemDataTags
                label="Responsibility"
                name="responsibility"
                variant="stacked"
                tooltip="What is the role of the business with regard to data processing?"
              />
              <SystemDataTextField
                name="dpo"
                id="dpo"
                label="Legal contact (DPO)"
                tooltip="What is the official privacy contact information?"
              />
              <SystemDataTextField
                label="Joint controller"
                name="joint_controller_info"
                tooltip="Who are the party or parties that share responsibility for processing data?"
                variant="stacked"
              />
              <SystemDataTextField
                label="Data security practices"
                name="data_security_practices"
                id="data_security_practices"
                tooltip="Which data security practices are employed to keep the data safe?"
              />
            </SystemDataGroup>
            {/* Data uses */}
            {initialValues.privacy_declarations &&
              initialValues.privacy_declarations.map((_, index) => (
                <>
                  <SystemDataGroup key={index} heading="Data use declaration">
                    <SystemDataTextField
                      id={`privacy_declarations[${index}].name`}
                      label="Declaration name (optional)"
                      name={`privacy_declarations[${index}].name`}
                      tooltip="Would you like to append anything to the system name?"
                      variant="stacked"
                    />
                    <SystemDataTextField
                      id={`privacy_declarations[${index}].data_use`}
                      name={`privacy_declarations[${index}].data_use`}
                      label="This system processes personal data"
                      tooltip="Does this system process personal data?"
                      variant="stacked"
                    />
                    <SystemDataTags
                      id={`privacy_declarations[${index}].data_categories`}
                      name={`privacy_declarations[${index}].data_categories`}
                      label="Data categories"
                      tooltip="Which categories of personal data are collected for this purpose?"
                      variant="stacked"
                    />
                    <SystemDataTags
                      id={`privacy_declarations[${index}].data_subjects`}
                      name={`privacy_declarations[${index}].data_subjects`}
                      label="Data subjects"
                      tooltip="Who are the subjects for this personal data?"
                      variant="stacked"
                    />
                    <SystemDataTextField
                      id={`privacy_declarations[${index}].legal_basis_for_processing`}
                      name={`privacy_declarations[${index}].legal_basis_for_processing`}
                      label="Legal basis for processing"
                      tooltip="What is the legal basis under which personal data is processed for this purpose?"
                      variant="stacked"
                    />
                    <SystemDataTextField
                      id={`privacy_declarations[${index}].impact_assessment_location`}
                      name={`privacy_declarations[${index}].impact_assessment_location`}
                      label="Impact assessment location"
                      tooltip="Where is the legitimate interest impact assessment stored?"
                      variant="stacked"
                    />
                    <SystemDataTextField
                      id={`privacy_declarations[${index}].retention_period`}
                      name={`privacy_declarations[${index}].retention_period`}
                      label="Retention period (days)"
                      tooltip="How long is personal data retained for this purpose?"
                      variant="stacked"
                    />
                  </SystemDataGroup>
                  <SystemDataGroup heading="Features">
                    <SystemDataTags
                      id={`privacy_declarations[${index}].features`}
                      name={`privacy_declarations[${index}].features`}
                      label="Features"
                      tooltip="What are some features of how data is processed?"
                      variant="stacked"
                    />
                  </SystemDataGroup>
                  <SystemDataGroup heading="Dataset reference">
                    <SystemDataTags
                      id={`privacy_declarations[${index}].dataset_references`}
                      name={`privacy_declarations[${index}].dataset_references`}
                      label="Dataset references"
                      tooltip="Is there a dataset configured for this system?"
                      variant="stacked"
                    />
                  </SystemDataGroup>
                  <SystemDataGroup heading="Special category data">
                    <SystemDataSwitch
                      id={`privacy_declarations[${index}].processes_special_category_data`}
                      name={`privacy_declarations[${index}].processes_special_category_data`}
                      label="This system processes special category data"
                      tooltip="Is this system processing special category data as defined by GDPR Article 9?"
                      variant="stacked"
                    />
                    <SystemDataTextField
                      id={`privacy_declarations[${index}].special_category_legal_basis`}
                      name={`privacy_declarations[${index}].special_category_legal_basis`}
                      label="Legal basis for processing"
                      tooltip="What is the legal basis under which the special category data is processed?"
                      variant="stacked"
                    />
                  </SystemDataGroup>
                  <SystemDataGroup heading="Third parties">
                    <SystemDataSwitch
                      id={`privacy_declarations[${index}].data_shared_with_third_parties`}
                      name={`privacy_declarations[${index}].data_shared_with_third_parties`}
                      label="This system shares data with 3rd parties for this purpose"
                      tooltip="Does this system disclose, sell, or share personal data collected for this business use with 3rd parties?"
                      variant="stacked"
                    />
                    <SystemDataTextField
                      id={`privacy_declarations[${index}].third_parties`}
                      name={`privacy_declarations[${index}].third_parties`}
                      label="Third parties"
                      tooltip="Which type of third parties is the data shared with?"
                      variant="stacked"
                    />
                    <SystemDataTags
                      id={`privacy_declarations[${index}].shared_categories`}
                      name={`privacy_declarations[${index}].shared_categories`}
                      label="Shared categories"
                      tooltip="Which categories of personal data does this system share with third parties?"
                      variant="stacked"
                    />
                  </SystemDataGroup>
                </>
              ))}
            {/* System flow */}
            <SystemDataGroup heading="Data flow">
              <SystemDataTags
                id="ingress"
                name="ingress"
                label="Sources"
                variant="stacked"
              />
              <SystemDataTags
                id="egress"
                name="egress"
                label="Destinations"
                variant="stacked"
              />
            </SystemDataGroup>
          </Stack>
        </Form>
      )}
    </Formik>
  );
};

export default SystemDataForm;
