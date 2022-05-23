import {
  Box,
  Button,
  Container,
  Flex,
  Heading,
  Image,
  Stack,
} from '@fidesui/react';
import type { NextPage } from 'next';
import Head from 'next/head';
import React from 'react';
import Header from '../features/common/Header';
import { ArrowDownLineIcon } from '../features/common/Icon';

const Setup: NextPage = () => (
  <Stack>
    {/* <Header username={session && session.username} /> */}
    <Container
      height="35vh"
      maxW="100vw"
      padding="0px"
      bg="blue.600"
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
      Get Started
      <div>
        Privacy engineering can seem like an endlessly complex confluence of
        legal and data engineering terminology - fear not; Fides is here to
        simplify this. This wizard will help you to very quickly configure
        Fidesctl and in doing so build your first data map. Along the way you'll
        learn the basic resources and concepts of privacy engineering with Fides
        so you can quickly apply in all your work.
      </div>
      <div>Let's get started!</div>
      <div>Guided Setup (Recommended)</div>
      <div>Skip (Power User)</div>
    </main>
  </Stack>
);

export default Setup;
