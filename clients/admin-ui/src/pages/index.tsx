import { Heading } from "@fidesui/react";
import type { NextPage } from "next";
import React from "react";

import Layout from "@/features/common/Layout";

const Home: NextPage = () => (
  <Layout title="Home">
    <main>
      <Heading mb={8} fontSize="2xl" fontWeight="semibold">
        Welcome home!
      </Heading>
    </main>
  </Layout>
);

// TODO: replace auth https://github.com/ethyca/fidesui/issues/2
// export const getServerSideProps = wrapper.getServerSideProps(
//   (store) => async (context) => {
//     const session = await getSession(context);
//     if (session && typeof session.accessToken !== 'undefined') {
//       await store.dispatch(assignToken(session.accessToken));
//       return { props: { session } };
//     }

//     // TODO: once user login is implemented in fides-ctl, re-enable this to make
//     // sure the home page is login-protected
//     return {
//       //   redirect: {
//       //     destination: '/login',
//       //     permanent: false,
//       //   },
//     };
//   }
// );

export default Home;
