import { Button, Container, Heading, Image, Stack } from "@fidesui/react";
import type { NextPage } from "next";
import React from "react";

const Setup: NextPage = () => (
  <Stack>
    <Container
      height="35vh"
      maxW="100vw"
      padding="0px"
      bg="white"
      color="white"
    >
      <Image
        boxSize="100%"
        // fallback={}
        objectFit="fill"
        // src=""
        alt="Data Map"
      />
    </Container>

    <main>
      <Stack px={9} py={10} spacing={6}>
        <Heading as="h3" size="lg">
          Get Started
        </Heading>
        <div>
          Privacy engineering can seem like an endlessly complex confluence of
          legal and data engineering terminology - fear not; Fides is here to
          simplify this. This wizard will help you to very quickly configure
          Fidesctl and in doing so build your first data map. Along the way
          you'll learn the basic resources and concepts of privacy engineering
          with Fides so you can quickly apply in all your work.
        </div>
        <div>Let's get started!</div>
        <Stack direction={["column", "row"]} spacing="24px">
          <Button
            bg="primary.800"
            _hover={{ bg: "primary.400" }}
            _active={{ bg: "primary.500" }}
            colorScheme="primary"
          >
            Guided Setup (Recommended)
          </Button>
          <Button variant="ghost" mr={4} colorScheme="complimentary">
            Skip (Power User)
          </Button>
        </Stack>
      </Stack>
    </main>
  </Stack>
);

export default Setup;
