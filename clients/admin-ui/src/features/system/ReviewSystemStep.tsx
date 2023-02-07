import {
  Box,
  Button,
  Divider,
  FormLabel,
  Heading,
  Stack,
  Text,
} from "@fidesui/react";
import { Form, Formik } from "formik";
import { Fragment } from "react";

import ReviewSystemFormExtension from "~/features/system/ReviewSystemFormExtension";
import { System } from "~/types/api";

import TaxonomyEntityTag from "../taxonomy/TaxonomyEntityTag";
import { ReviewItem } from "./form-layout";
import PrivacyDeclarationAccordion from "./PrivacyDeclarationAccordion";

interface Props {
  system: System;
  onSuccess: () => void;
  onCancel: () => void;
  abridged?: boolean;
}

const ReviewSystemStep = ({ system, onSuccess, onCancel, abridged }: Props) => {
  const handleSubmit = () => {
    onSuccess();
  };

  return (
    <Formik initialValues={system} enableReinitialize onSubmit={handleSubmit}>
      <Form>
        <Stack spacing={10}>
          <Heading as="h3" size="lg" data-testid="review-heading">
            {/* TODO FUTURE: Path when describing system from infra scanning */}
            Review declaration for manual system
          </Heading>
          <Text mt="10px !important">
            Let’s quickly review our declaration before registering
          </Text>
          <Stack spacing={4}>
            <ReviewItem label="System name">
              <Text>{system.name}</Text>
            </ReviewItem>
            <ReviewItem label="System key">
              <Text>{system.fides_key}</Text>
            </ReviewItem>
            <ReviewItem label="System description">
              <Text>{system.description}</Text>
            </ReviewItem>
            <ReviewItem label="System type">
              <Text>{system.system_type}</Text>
            </ReviewItem>
            <ReviewItem label="System tags">
              {system.tags?.map((tag) => (
                <TaxonomyEntityTag key={tag} name={tag} mr={1} />
              ))}
            </ReviewItem>
            <ReviewItem label="System dependencies">
              {system.system_dependencies?.map((dep) => (
                <TaxonomyEntityTag key={dep} name={dep} mr={1} />
              ))}
            </ReviewItem>
            {!abridged ? <ReviewSystemFormExtension system={system} /> : null}

            <FormLabel fontWeight="semibold">Privacy declarations:</FormLabel>
            {system.privacy_declarations.map((declaration) => (
              <Fragment key={declaration.name}>
                <Divider />
                <PrivacyDeclarationAccordion
                  abridged={abridged}
                  privacyDeclaration={declaration}
                />
              </Fragment>
            ))}
          </Stack>
          <Box>
            <Button
              onClick={onCancel}
              mr={2}
              size="sm"
              variant="outline"
              data-testid="back-btn"
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
export default ReviewSystemStep;
