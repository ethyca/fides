import { Button, Container, Heading, Image, Stack } from "@fidesui/react";
import { useRouter } from "next/router";

import { useAppDispatch } from "~/app/hooks";
import { SYSTEM_ROUTE } from "~/constants";

import { changeStep } from "./config-wizard.slice";

const Setup = () => {
  const router = useRouter();
  const dispatch = useAppDispatch();

  return (
    <Stack data-testid="setup" mr={-14}>
      <Container height="35vh" maxW="100vw" bg="white" color="white">
        <Image
          boxSize="100%"
          objectFit="cover"
          src="/images/config_splash.svg"
          alt="Data Map"
        />
      </Container>

      <Stack spacing={6} position="absolute" maxWidth="50%" minWidth="600px">
        <Heading as="h3" size="lg">
          Generate your Data Map
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
            onClick={() => dispatch(changeStep())}
            data-testid="guided-setup-btn"
          >
            Generate a Map Automatically (recommended)
          </Button>
          <Button
            variant="ghost"
            mr={4}
            colorScheme="complimentary"
            onClick={() => router.push(SYSTEM_ROUTE)}
          >
            Skip (Power User)
          </Button>
        </Stack>
      </Stack>
    </Stack>
  );
};

export default Setup;
