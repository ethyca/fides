import Head from 'next/head';
import React from 'react';

import {BASE_ASSET_URN} from "../../constants"



const FidesHead = () => (
    <Head>
    <title>fidesops</title>
    <meta name='description' content='admin ui' />
    <link rel='icon' href={`${BASE_ASSET_URN}/favicon.ico`} />
  </Head> 
  );

export default FidesHead;
