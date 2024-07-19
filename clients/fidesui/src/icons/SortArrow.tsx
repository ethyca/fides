import { Icon } from "@chakra-ui/icon";
import React from "react";

type SortArrowProps = {
  up?: boolean;
};

const SortArrow = ({ up }: SortArrowProps) => {
  if (up === undefined) {
    return (
      <Icon width="24px" height="26px" viewBox="0 0 24 26" fill="none">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="24"
          height="26"
          viewBox="0 0 24 26"
          fill="none"
        >
          <path
            d="M8.72726 15.129L10.9716 12.8145L12 13.875L7.99998 18L4 13.875L5.02837 12.8145L7.27271 15.129V6H8.72726V15.129Z"
            fill="#2D3748"
          />
          <path
            d="M16.7523 8.871V18H15.3089V8.871L13.0205 11.25L12 10.1895L16.0306 6L20 10.125L18.9795 11.1855L16.7523 8.871Z"
            fill="#2D3748"
          />
        </svg>
      </Icon>
    );
  }

  if (up) {
    return (
      <Icon
        width="24px"
        height="26px"
        viewBox="0 0 24 26"
        fill="none"
        style={{
          transform: "rotate(180deg)",
        }}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="24"
          height="26"
          viewBox="0 0 24 26"
          fill="none"
        >
          <g filter="url(#filter0_d_3399_48680)">
            <path
              d="M8.72726 15.129L10.9716 12.8145L12 13.875L7.99998 18L4 13.875L5.02837 12.8145L7.27271 15.129V6H8.72726V15.129Z"
              fill="#2D3748"
            />
            <path
              d="M8.22726 15.129V16.3629L9.08621 15.4771L10.9716 13.5327L11.3035 13.875L7.99998 17.2818L4.69648 13.875L5.02837 13.5327L6.91375 15.4771L7.77271 16.3629V15.129V6.5H8.22726V15.129Z"
              stroke="black"
            />
          </g>
          <path
            d="M16.7523 8.871V18H15.3089V8.871L13.0205 11.25L12 10.1895L16.0306 6L20 10.125L18.9795 11.1855L16.7523 8.871Z"
            fill="#2D3748"
          />
          <defs>
            <filter
              id="filter0_d_3399_48680"
              x="0"
              y="6"
              width="16"
              height="20"
              filterUnits="userSpaceOnUse"
              colorInterpolationFilters="sRGB"
            >
              <feFlood floodOpacity="0" result="BackgroundImageFix" />
              <feColorMatrix
                in="SourceAlpha"
                type="matrix"
                values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0"
                result="hardAlpha"
              />
              <feOffset dy="4" />
              <feGaussianBlur stdDeviation="2" />
              <feComposite in2="hardAlpha" operator="out" />
              <feColorMatrix
                type="matrix"
                values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0.25 0"
              />
              <feBlend
                mode="normal"
                in2="BackgroundImageFix"
                result="effect1_dropShadow_3399_48680"
              />
              <feBlend
                mode="normal"
                in="SourceGraphic"
                in2="effect1_dropShadow_3399_48680"
                result="shape"
              />
            </filter>
          </defs>
        </svg>
      </Icon>
    );
  }

  return (
    <Icon width="24px" height="26px" viewBox="0 0 24 26" fill="none">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="24"
        height="26"
        viewBox="0 0 24 26"
        fill="none"
      >
        <g filter="url(#filter0_d_3399_48680)">
          <path
            d="M8.72726 15.129L10.9716 12.8145L12 13.875L7.99998 18L4 13.875L5.02837 12.8145L7.27271 15.129V6H8.72726V15.129Z"
            fill="#2D3748"
          />
          <path
            d="M8.22726 15.129V16.3629L9.08621 15.4771L10.9716 13.5327L11.3035 13.875L7.99998 17.2818L4.69648 13.875L5.02837 13.5327L6.91375 15.4771L7.77271 16.3629V15.129V6.5H8.22726V15.129Z"
            stroke="black"
          />
        </g>
        <path
          d="M16.7523 8.871V18H15.3089V8.871L13.0205 11.25L12 10.1895L16.0306 6L20 10.125L18.9795 11.1855L16.7523 8.871Z"
          fill="#2D3748"
        />
        <defs>
          <filter
            id="filter0_d_3399_48680"
            x="0"
            y="6"
            width="16"
            height="20"
            filterUnits="userSpaceOnUse"
            colorInterpolationFilters="sRGB"
          >
            <feFlood floodOpacity="0" result="BackgroundImageFix" />
            <feColorMatrix
              in="SourceAlpha"
              type="matrix"
              values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0"
              result="hardAlpha"
            />
            <feOffset dy="4" />
            <feGaussianBlur stdDeviation="2" />
            <feComposite in2="hardAlpha" operator="out" />
            <feColorMatrix
              type="matrix"
              values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0.25 0"
            />
            <feBlend
              mode="normal"
              in2="BackgroundImageFix"
              result="effect1_dropShadow_3399_48680"
            />
            <feBlend
              mode="normal"
              in="SourceGraphic"
              in2="effect1_dropShadow_3399_48680"
              result="shape"
            />
          </filter>
        </defs>
      </svg>
    </Icon>
  );
};

export default SortArrow;
