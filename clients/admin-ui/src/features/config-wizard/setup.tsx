import { Button, Container, Heading, Image, Stack } from "@fidesui/react";
import { useRouter } from "next/router";
import React from "react";

interface Props {
  wizardStep: Function;
}

const Setup = ({ wizardStep }: Props) => {
  const router = useRouter();
  return (
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
            you&apos;ll learn the basic resources and concepts of privacy
            engineering with Fides so you can quickly apply in all your work.
          </div>
          <div>Let&apos;s get started!</div>
          <Stack direction={["column", "row"]} spacing="24px">
            <Button
              variant="primary"
              onClick={() => wizardStep(true)}
              data-testid="guided-setup-btn"
            >
              Guided Setup (Recommended)
            </Button>
            <Button
              variant="ghost"
              mr={4}
              colorScheme="complimentary"
              onClick={() => router.push("/")}
            >
              Skip (Power User)
            </Button>
          </Stack>
        </Stack>
      </main>
    </Stack>
  );
};

export default Setup;
