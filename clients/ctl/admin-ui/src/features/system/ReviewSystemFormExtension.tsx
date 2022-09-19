import { Box, FormLabel, Grid, GridItem, Text } from "@fidesui/react";
import React, { ReactNode } from "react";

import TaxonomyEntityTag from "~/features/taxonomy/TaxonomyEntityTag";
import { System } from "~/types/api";

export const ReviewItem = ({
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

const ReviewSystemFormExtension = ({ system }: { system: System }) => (
  <>
    <ReviewItem label="Data responsibility title">
      <Text>{system.data_responsibility_title}</Text>
    </ReviewItem>
    <ReviewItem label="Administrating department">
      <Text>{system.administrating_department}</Text>
    </ReviewItem>
    <ReviewItem label="Geographic location">
      {system.third_country_transfers?.map((country) => (
        <TaxonomyEntityTag key={country} name={country} mr={1} />
      ))}
    </ReviewItem>
    {system.joint_controller ? (
      <Box data-testid="review-Joint controller">
        <FormLabel fontWeight="semibold">Joint controller</FormLabel>
        <Box ml={8}>
          <ReviewItem label="Name">
            <Text>{system.joint_controller.name}</Text>
          </ReviewItem>
          <ReviewItem label="Address">
            <Text>{system.joint_controller.address}</Text>
          </ReviewItem>
          <ReviewItem label="Email">
            <Text>{system.joint_controller.email}</Text>
          </ReviewItem>
          <ReviewItem label="Phone">
            <Text>{system.joint_controller.phone}</Text>
          </ReviewItem>
        </Box>
      </Box>
    ) : (
      <ReviewItem label="Joint controller">None</ReviewItem>
    )}
    {system.data_protection_impact_assessment ? (
      <Box data-testid="review-Data protection impact assessment">
        <FormLabel fontWeight="semibold">
          Data protection impact assessment
        </FormLabel>
        <Box ml={8}>
          <ReviewItem label="Is required">
            <Text>
              {system.data_protection_impact_assessment.is_required
                ? "Yes"
                : "No"}
            </Text>
          </ReviewItem>
          <ReviewItem label="Progress">
            <Text>{system.data_protection_impact_assessment.progress}</Text>
          </ReviewItem>
          <ReviewItem label="Link">
            <Text>{system.data_protection_impact_assessment.link}</Text>
          </ReviewItem>
        </Box>
      </Box>
    ) : (
      <ReviewItem label="Data protection impact assessment">None</ReviewItem>
    )}
  </>
);

export default ReviewSystemFormExtension;
