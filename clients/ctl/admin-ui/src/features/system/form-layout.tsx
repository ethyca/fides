import { FormLabel, Grid, GridItem, Text } from "@fidesui/react";
import React, { ReactNode } from "react";

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

export const DeclarationItem = ({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) => (
  <Grid templateColumns="1fr 2fr" data-testid={`declaration-${label}`}>
    <GridItem>
      <Text color="gray.600">{label}</Text>
    </GridItem>
    <GridItem>{children}</GridItem>
  </Grid>
);
