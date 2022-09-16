import {
  Box,
  Button,
  Divider,
  FormLabel,
  Grid,
  GridItem,
  Heading,
  Stack,
  Text,
} from "@fidesui/react";
import { Form, Formik } from "formik";
import React, { Fragment, ReactNode } from "react";

import {
  DEFAULT_ORGANIZATION_FIDES_KEY,
  useGetOrganizationByFidesKeyQuery,
} from "~/features/organization";
import { System } from "~/types/api";

import TaxonomyEntityTag from "../taxonomy/TaxonomyEntityTag";
import PrivacyDeclarationAccordion from "./PrivacyDeclarationAccordion";

const ReviewItem = ({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) => (
  <Grid templateColumns="1fr 2fr" data-testid={`review-${label}`}>
    <GridItem>
      <FormLabel fontWeight="semibold" m={0}>
        {label}:
      </FormLabel>
    </GridItem>
    <GridItem>{children}</GridItem>
  </Grid>
);

interface Props {
  system: System;
  onCancel: () => void;
  onSuccess: () => void;
  abridged?: boolean;
}

const ReviewSystemForm = ({ system, onCancel, onSuccess, abridged }: Props) => {
  const { data: existingOrg } = useGetOrganizationByFidesKeyQuery(
    DEFAULT_ORGANIZATION_FIDES_KEY
  );

  const initialValues = {
    name: existingOrg?.name ?? "",
    system_name: system.name ?? "",
    system_key: system.fides_key ?? "",
    system_description: system.description ?? "",
    system_type: system.system_type ?? "",
    tags: system.tags ?? [],
    privacy_declarations: system.privacy_declarations ?? [],
    system_dependencies: system.system_dependencies ?? [],
    administrating_department: system.administrating_department ?? "",
    third_country_transfers: system.third_country_transfers ?? [],
    joint_controller: system.joint_controller,
    data_protection_impact_assessment: system.data_protection_impact_assessment,
    data_responsibility_title: system.data_responsibility_title ?? "",
  };

  const handleSubmit = () => {
    onSuccess();
  };

  return (
    <Formik
      initialValues={initialValues}
      enableReinitialize
      onSubmit={handleSubmit}
    >
      <Form>
        <Stack spacing={10}>
          <Heading as="h3" size="lg" data-testid="review-heading">
            {/* TODO FUTURE: Path when describing system from infra scanning */}
            Review {existingOrg?.name}
          </Heading>
          <Text mt="10px !important">
            Let’s quickly review our declaration before registering
          </Text>
          <Stack spacing={4}>
            <ReviewItem label="System name">
              <Text>{initialValues.system_name}</Text>
            </ReviewItem>
            <ReviewItem label="System key">
              <Text>{initialValues.system_key}</Text>
            </ReviewItem>
            <ReviewItem label="System description">
              <Text>{initialValues.system_description}</Text>
            </ReviewItem>
            <ReviewItem label="System type">
              <Text>{initialValues.system_type}</Text>
            </ReviewItem>
            <ReviewItem label="System tags">
              {initialValues.tags.map((tag) => (
                <TaxonomyEntityTag key={tag} name={tag} mr={1} />
              ))}
            </ReviewItem>
            <ReviewItem label="System dependencies">
              {initialValues.system_dependencies.map((dep) => (
                <TaxonomyEntityTag key={dep} name={dep} mr={1} />
              ))}
            </ReviewItem>
            {!abridged ? (
              <>
                <ReviewItem label="Data responsibility title">
                  <Text>{initialValues.data_responsibility_title}</Text>
                </ReviewItem>
                <ReviewItem label="Administrating department">
                  <Text>{initialValues.administrating_department}</Text>
                </ReviewItem>
                <ReviewItem label="Geographic location">
                  {initialValues.third_country_transfers.map((country) => (
                    <TaxonomyEntityTag key={country} name={country} mr={1} />
                  ))}
                </ReviewItem>
                {initialValues.joint_controller ? (
                  <Box data-testid="review-Joint controller">
                    <FormLabel fontWeight="semibold">
                      Joint controller
                    </FormLabel>
                    <Box ml={8}>
                      <ReviewItem label="Name">
                        <Text>{initialValues.joint_controller.name}</Text>
                      </ReviewItem>
                      <ReviewItem label="Address">
                        <Text>{initialValues.joint_controller.address}</Text>
                      </ReviewItem>
                      <ReviewItem label="Email">
                        <Text>{initialValues.joint_controller.email}</Text>
                      </ReviewItem>
                      <ReviewItem label="Phone">
                        <Text>{initialValues.joint_controller.phone}</Text>
                      </ReviewItem>
                    </Box>
                  </Box>
                ) : (
                  <ReviewItem label="Joint controller">None</ReviewItem>
                )}
                {initialValues.data_protection_impact_assessment ? (
                  <Box data-testid="review-Data protection impact assessment">
                    <FormLabel fontWeight="semibold">
                      Data protection impact assessment
                    </FormLabel>
                    <Box ml={8}>
                      <ReviewItem label="Is required">
                        <Text>
                          {initialValues.data_protection_impact_assessment
                            .is_required
                            ? "Yes"
                            : "No"}
                        </Text>
                      </ReviewItem>
                      <ReviewItem label="Progress">
                        <Text>
                          {
                            initialValues.data_protection_impact_assessment
                              .progress
                          }
                        </Text>
                      </ReviewItem>
                      <ReviewItem label="Link">
                        <Text>
                          {initialValues.data_protection_impact_assessment.link}
                        </Text>
                      </ReviewItem>
                    </Box>
                  </Box>
                ) : (
                  <ReviewItem label="Data protection impact assessment">
                    None
                  </ReviewItem>
                )}
              </>
            ) : null}
            <FormLabel fontWeight="semibold">Privacy declarations:</FormLabel>
            {initialValues.privacy_declarations.map((declaration) => (
              <Fragment key={declaration.name}>
                <Divider />
                <PrivacyDeclarationAccordion privacyDeclaration={declaration} />
              </Fragment>
            ))}
          </Stack>
          <Box>
            <Button
              onClick={() => onCancel()}
              mr={2}
              size="sm"
              variant="outline"
              data-testid="cancel-btn"
            >
              Cancel
            </Button>
            {/* TODO FUTURE: This button doesn't do any registering yet until data maps are added */}
            <Button
              type="submit"
              colorScheme="primary"
              mr={2}
              size="sm"
              data-testid="confirm-btn"
            >
              Confirm and Register
            </Button>
          </Box>
        </Stack>
      </Form>
    </Formik>
  );
};
export default ReviewSystemForm;
