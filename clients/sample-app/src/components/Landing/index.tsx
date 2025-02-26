/* eslint-disable react/no-unescaped-entities */
/* eslint-disable react/jsx-no-target-blank */
import Image from "next/image";

import landingImage from "../../../public/landing-box-transparent.png";
import css from "./style.module.scss";
import WhatInTheBox from "./WhatInTheBox";

const Landing = () => (
  <div className={css.wrapper}>
    <style jsx global>
      {"body { background-color: #01020D; }"}
    </style>
    <div className={css.content}>
      <div className={css.headingContent}>
        <Image src={landingImage} width={1860} alt="" className={css.box} />
        <h1>Welcome to Fides!</h1>
        <p className={css.subhead}>
          Let's run our first privacy request in under 5 minutes
        </p>
      </div>
      <main>
        <h2>What's in the box?</h2>
        <p className={css.subhead}>
          You've deployed Fides and the "Cookie House" sample project.
          <br />
          Click any of the links below to explore!
        </p>
        <div className={css.items}>
          <div className={css.item}>
            <div className={css.border} />
            <h5>FIDES</h5>
            <p>
              This is the webserver and Admin UI to manage Fides, including
              administering privacy requests (and more!)
            </p>
            <p>
              Username: <strong>root_user</strong>
              <br />
              Password: <strong>Testpassword1!</strong>
            </p>
            <p>
              <a href="http://localhost:8080" target="_blank">
                http://localhost:8080
              </a>
            </p>
          </div>
          <div className={css.item}>
            <div className={css.border} />
            <h5>SAMPLE PROJECT</h5>
            <p>
              This is the "Cookie House" sample project, which is a basic
              eCommerce site you can use to collect user data.
            </p>
            <p>
              Buy a cookie and provide some sample personal data to try it out.
            </p>
            <p>
              <a href="http://localhost:3000" target="_blank">
                http://localhost:3000
              </a>
            </p>
          </div>
          <div className={css.item}>
            <div className={css.border} />
            <h5>PRIVACY CENTER</h5>
            <p>
              This is where users can submit privacy requests to Fides. It's
              been customized to match the "Cookie House" project.
            </p>
            <p>
              Try submitting a "Download your data" request for{" "}
              <strong>"jane@example.com"</strong>.
            </p>
            <p>
              <a href="http://localhost:3001" target="_blank">
                http://localhost:3001
              </a>
            </p>
          </div>
          <div className={css.item}>
            <div className={css.border} />
            <h5>DSR DIRECTORY</h5>
            <p>
              Fides can send results via email. For this project, they are saved
              to a directory on your computer.
            </p>
            <p>
              Approve your request in the Fides UI, then open{" "}
              <strong>"fides_uploads"</strong> to view.
            </p>
          </div>
        </div>
      </main>
    </div>
    <WhatInTheBox />
    <footer>
      <div className={css.links}>
        <a href="https://ethyca.com/book-demo">Book a Demo</a>
        <a href="https://fid.es/join-slack">
          Join the Fides Open-Source Community
        </a>
      </div>
      <Image
        className={css.separator}
        src="/line-16.svg"
        width={1860}
        height={2}
        alt=""
      />

      <svg
        className={css.fides}
        width="108"
        height="33"
        viewBox="0 0 108 33"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <g clipPath="url(#clip0_1_2658)">
          <path d="M33.5081 0H0.962402V32.5457H33.5081V0Z" fill="white" />
          <path
            d="M53.7521 8.91117C54.3019 8.92157 54.845 9.03447 55.3533 9.24408L56.1779 5.86904C55.1907 5.50533 54.1471 5.31854 53.095 5.31726C48.9225 5.31726 47.4115 7.99522 47.4115 11.2544V12.0545H44.231V15.6447H47.417V27.5024H51.9944V15.6484H55.2687V12.0581H51.9944V11.1256C51.9944 9.52365 52.6478 8.91117 53.7521 8.91117Z"
            fill="white"
          />
          <path
            d="M73.4775 5.69434H78.0475V27.5024H73.4775V25.9722C72.3842 27.0628 71.256 27.8776 69.7652 27.8776C65.9222 27.8776 63.443 24.8281 63.443 19.7849C63.443 14.7416 66.5976 11.6922 69.8535 11.6922C71.556 11.6922 72.4302 12.3249 73.4775 13.3052V5.69434ZM73.4775 22.7571V16.408C72.7791 15.7706 71.865 15.421 70.9192 15.4295C69.4357 15.4295 68.1363 16.7979 68.1363 19.7352C68.1363 22.7663 69.1836 24.1329 70.9578 24.1329C71.9315 24.1329 72.7192 23.7632 73.4775 22.7498V22.7571Z"
            fill="white"
          />
          <path
            d="M94.7555 25.7201L96.8206 22.8674C98.2212 23.925 99.5132 24.4896 100.807 24.4896C102.171 24.4896 102.76 23.971 102.76 23.1617C102.76 22.1427 101.227 21.6811 99.631 21.0594C97.7371 20.3237 95.5414 19.0693 95.5414 16.5183C95.5414 13.6417 97.8789 11.6829 101.444 11.6829C103.813 11.6829 105.576 12.6393 106.894 13.6398L104.842 16.3858C103.737 15.5894 102.659 15.0671 101.589 15.0671C100.406 15.0671 99.8225 15.5324 99.8225 16.3012C99.8225 17.2871 101.269 17.6641 102.87 18.2453C104.829 18.97 107.035 20.068 107.035 22.8913C107.035 25.7146 104.827 27.8757 100.688 27.8757C98.65 27.8775 96.3199 26.9929 94.7555 25.7201Z"
            fill="white"
          />
          <path
            d="M57.1222 12.0582H61.7033V27.508H57.1222V12.0582Z"
            fill="white"
          />
          <path
            d="M59.4247 10.0368C60.6964 10.0368 61.7272 9.00661 61.7272 7.73585C61.7272 6.46509 60.6964 5.43494 59.4247 5.43494C58.1531 5.43494 57.1222 6.46509 57.1222 7.73585C57.1222 9.00661 58.1531 10.0368 59.4247 10.0368Z"
            fill="white"
          />
          <path
            d="M87.642 27.9493C86.5747 27.9597 85.5145 27.7758 84.5131 27.4067C83.5785 27.0626 82.7274 26.5248 82.0155 25.8286C81.2866 25.1025 80.7174 24.2324 80.3443 23.2739C79.9188 22.1786 79.7101 21.0111 79.7296 19.8363C79.711 18.6752 79.925 17.522 80.359 16.4447C80.7434 15.4955 81.3056 14.6284 82.0155 13.89C82.6811 13.2017 83.4785 12.6543 84.3603 12.2807C85.2601 11.9073 86.2255 11.7178 87.1997 11.7231C88.174 11.7285 89.1372 11.9287 90.0328 12.3119C90.842 12.6819 91.5554 13.2325 92.1181 13.9213C92.684 14.6299 93.106 15.4421 93.3605 16.3123C93.6402 17.2567 93.7791 18.2371 93.7728 19.222C93.7742 19.667 93.749 20.1117 93.6973 20.5536C93.6458 20.9675 93.5997 21.2654 93.5593 21.4512H84.8205C85.0659 22.3806 85.5051 23.0262 86.1383 23.3879C86.8239 23.7613 87.5958 23.9478 88.3763 23.9287C88.9016 23.9296 89.4241 23.8515 89.9261 23.6969C90.4757 23.5213 91.0051 23.2876 91.5052 22.9999L93.4433 25.9721C92.5293 26.6342 91.5186 27.1516 90.4469 27.506C89.5379 27.7866 88.5933 27.9358 87.642 27.9493ZM84.7597 17.9787H89.2966C89.3092 17.4249 89.1546 16.8801 88.853 16.4153C88.5549 15.9702 88.0076 15.7477 87.2113 15.7477C86.6495 15.7376 86.1019 15.9243 85.6634 16.2755C85.2242 16.6238 84.9229 17.1915 84.7597 17.9787Z"
            fill="white"
          />
        </g>
        <defs>
          <clipPath id="clip0_1_2658">
            <rect
              width="106.075"
              height="32.5457"
              fill="white"
              transform="translate(0.962402)"
            />
          </clipPath>
        </defs>
      </svg>
    </footer>
  </div>
);

export default Landing;
