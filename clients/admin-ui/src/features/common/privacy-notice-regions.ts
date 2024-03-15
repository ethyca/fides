import { PrivacyNoticeRegion } from "~/types/api";

/**
 * A mapping of privacy notice regions to human readable names.
 *
 * The typing is important here so that our build will fail if we are missing a region.
 */
export const PRIVACY_NOTICE_REGION_RECORD: Record<PrivacyNoticeRegion, string> =
  {
    [PrivacyNoticeRegion.ER]: "Eritrea",
    [PrivacyNoticeRegion.DJ]: "Djibouti",
    [PrivacyNoticeRegion.MR]: "Mauritania",
    [PrivacyNoticeRegion.NA]: "Namibia",
    [PrivacyNoticeRegion.GH]: "Ghana",
    [PrivacyNoticeRegion.SS]: "South Sudan",
    [PrivacyNoticeRegion.SC]: "Seychelles",
    [PrivacyNoticeRegion.IO]: "British Indian Ocean Territory",
    [PrivacyNoticeRegion.GQ]: "Equatorial Guinea",
    [PrivacyNoticeRegion.AO]: "Angola",
    [PrivacyNoticeRegion.CG]: "Republic of the Congo",
    [PrivacyNoticeRegion.BW]: "Botswana",
    [PrivacyNoticeRegion.BI]: "Burundi",
    [PrivacyNoticeRegion.DZ]: "Algeria",
    [PrivacyNoticeRegion.TD]: "Chad",
    [PrivacyNoticeRegion.NG]: "Nigeria",
    [PrivacyNoticeRegion.TZ]: "Tanzania",
    [PrivacyNoticeRegion.EH]: "Western Sahara",
    [PrivacyNoticeRegion.SN]: "Senegal",
    [PrivacyNoticeRegion.LR]: "Liberia",
    [PrivacyNoticeRegion.ZA]: "South Africa",
    [PrivacyNoticeRegion.CV]: "Cape Verde",
    [PrivacyNoticeRegion.GM]: "Gambia",
    [PrivacyNoticeRegion.SD]: "Sudan",
    [PrivacyNoticeRegion.KM]: "Comoros",
    [PrivacyNoticeRegion.SZ]: "Eswatini",
    [PrivacyNoticeRegion.UG]: "Uganda",
    [PrivacyNoticeRegion.MG]: "Madagascar",
    [PrivacyNoticeRegion.RW]: "Rwanda",
    [PrivacyNoticeRegion.CD]: "DR Congo",
    [PrivacyNoticeRegion.CM]: "Cameroon",
    [PrivacyNoticeRegion.SH]: "Saint Helena, Ascension and Tristan da Cunha",
    [PrivacyNoticeRegion.TG]: "Togo",
    [PrivacyNoticeRegion.MU]: "Mauritius",
    [PrivacyNoticeRegion.NE]: "Niger",
    [PrivacyNoticeRegion.BJ]: "Benin",
    [PrivacyNoticeRegion.EG]: "Egypt",
    [PrivacyNoticeRegion.LS]: "Lesotho",
    [PrivacyNoticeRegion.ET]: "Ethiopia",
    [PrivacyNoticeRegion.MA]: "Morocco",
    [PrivacyNoticeRegion.YT]: "Mayotte",
    [PrivacyNoticeRegion.BF]: "Burkina Faso",
    [PrivacyNoticeRegion.RE]: "Réunion",
    [PrivacyNoticeRegion.ST]: "São Tomé and Príncipe",
    [PrivacyNoticeRegion.CF]: "Central African Republic",
    [PrivacyNoticeRegion.MZ]: "Mozambique",
    [PrivacyNoticeRegion.MW]: "Malawi",
    [PrivacyNoticeRegion.ML]: "Mali",
    [PrivacyNoticeRegion.ZM]: "Zambia",
    [PrivacyNoticeRegion.LY]: "Libya",
    [PrivacyNoticeRegion.GW]: "Guinea-Bissau",
    [PrivacyNoticeRegion.SO]: "Somalia",
    [PrivacyNoticeRegion.KE]: "Kenya",
    [PrivacyNoticeRegion.GN]: "Guinea",
    [PrivacyNoticeRegion.ZW]: "Zimbabwe",
    [PrivacyNoticeRegion.TN]: "Tunisia",
    [PrivacyNoticeRegion.SL]: "Sierra Leone",
    [PrivacyNoticeRegion.GA]: "Gabon",
    [PrivacyNoticeRegion.CI]: "Ivory Coast",
    [PrivacyNoticeRegion.JO]: "Jordan",
    [PrivacyNoticeRegion.PK]: "Pakistan",
    [PrivacyNoticeRegion.KP]: "North Korea",
    [PrivacyNoticeRegion.MO]: "Macau",
    [PrivacyNoticeRegion.AM]: "Armenia",
    [PrivacyNoticeRegion.SY]: "Syria",
    [PrivacyNoticeRegion.TJ]: "Tajikistan",
    [PrivacyNoticeRegion.SA]: "Saudi Arabia",
    [PrivacyNoticeRegion.KR]: "South Korea",
    [PrivacyNoticeRegion.NP]: "Nepal",
    [PrivacyNoticeRegion.PH]: "Philippines",
    [PrivacyNoticeRegion.IQ]: "Iraq",
    [PrivacyNoticeRegion.LB]: "Lebanon",
    [PrivacyNoticeRegion.MN]: "Mongolia",
    [PrivacyNoticeRegion.PS]: "Palestine",
    [PrivacyNoticeRegion.YE]: "Yemen",
    [PrivacyNoticeRegion.JP]: "Japan",
    [PrivacyNoticeRegion.KZ]: "Kazakhstan",
    [PrivacyNoticeRegion.LK]: "Sri Lanka",
    [PrivacyNoticeRegion.MM]: "Myanmar",
    [PrivacyNoticeRegion.KG]: "Kyrgyzstan",
    [PrivacyNoticeRegion.CN]: "China",
    [PrivacyNoticeRegion.AF]: "Afghanistan",
    [PrivacyNoticeRegion.OM]: "Oman",
    [PrivacyNoticeRegion.IN]: "India",
    [PrivacyNoticeRegion.LA]: "Laos",
    [PrivacyNoticeRegion.UZ]: "Uzbekistan",
    [PrivacyNoticeRegion.MV]: "Maldives",
    [PrivacyNoticeRegion.ID]: "Indonesia",
    [PrivacyNoticeRegion.VN]: "Vietnam",
    [PrivacyNoticeRegion.MY]: "Malaysia",
    [PrivacyNoticeRegion.TW]: "Taiwan",
    [PrivacyNoticeRegion.KH]: "Cambodia",
    [PrivacyNoticeRegion.AE]: "United Arab Emirates",
    [PrivacyNoticeRegion.HK]: "Hong Kong",
    [PrivacyNoticeRegion.GE]: "Georgia",
    [PrivacyNoticeRegion.BD]: "Bangladesh",
    [PrivacyNoticeRegion.KW]: "Kuwait",
    [PrivacyNoticeRegion.TM]: "Turkmenistan",
    [PrivacyNoticeRegion.QA]: "Qatar",
    [PrivacyNoticeRegion.BH]: "Bahrain",
    [PrivacyNoticeRegion.BN]: "Brunei",
    [PrivacyNoticeRegion.TH]: "Thailand",
    [PrivacyNoticeRegion.BT]: "Bhutan",
    [PrivacyNoticeRegion.SG]: "Singapore",
    [PrivacyNoticeRegion.IL]: "Israel",
    [PrivacyNoticeRegion.AZ]: "Azerbaijan",
    [PrivacyNoticeRegion.TL]: "Timor-Leste",
    [PrivacyNoticeRegion.IR]: "Iran",
    [PrivacyNoticeRegion.TR]: "Turkey",
    [PrivacyNoticeRegion.MK]: "North Macedonia",
    [PrivacyNoticeRegion.IE]: "Ireland",
    [PrivacyNoticeRegion.DK]: "Denmark",
    [PrivacyNoticeRegion.SK]: "Slovakia",
    [PrivacyNoticeRegion.MD]: "Moldova",
    [PrivacyNoticeRegion.AX]: "Åland Islands",
    [PrivacyNoticeRegion.PL]: "Poland",
    [PrivacyNoticeRegion.BA]: "Bosnia and Herzegovina",
    [PrivacyNoticeRegion.SM]: "San Marino",
    [PrivacyNoticeRegion.CZ]: "Czechia",
    [PrivacyNoticeRegion.EE]: "Estonia",
    [PrivacyNoticeRegion.XK]: "Kosovo",
    [PrivacyNoticeRegion.FO]: "Faroe Islands",
    [PrivacyNoticeRegion.SJ]: "Svalbard and Jan Mayen",
    [PrivacyNoticeRegion.GG]: "Guernsey",
    [PrivacyNoticeRegion.FR]: "France",
    [PrivacyNoticeRegion.NL]: "Netherlands",
    [PrivacyNoticeRegion.FI]: "Finland",
    [PrivacyNoticeRegion.PT]: "Portugal",
    [PrivacyNoticeRegion.DE]: "Germany",
    [PrivacyNoticeRegion.MT]: "Malta",
    [PrivacyNoticeRegion.JE]: "Jersey",
    [PrivacyNoticeRegion.IS]: "Iceland",
    [PrivacyNoticeRegion.ES]: "Spain",
    [PrivacyNoticeRegion.GI]: "Gibraltar",
    [PrivacyNoticeRegion.NO]: "Norway",
    [PrivacyNoticeRegion.CY]: "Cyprus",
    [PrivacyNoticeRegion.RS]: "Serbia",
    [PrivacyNoticeRegion.LT]: "Lithuania",
    [PrivacyNoticeRegion.MC]: "Monaco",
    [PrivacyNoticeRegion.LU]: "Luxembourg",
    [PrivacyNoticeRegion.UA]: "Ukraine",
    [PrivacyNoticeRegion.IM]: "Isle of Man",
    [PrivacyNoticeRegion.RO]: "Romania",
    [PrivacyNoticeRegion.BE]: "Belgium",
    [PrivacyNoticeRegion.SE]: "Sweden",
    [PrivacyNoticeRegion.ME]: "Montenegro",
    [PrivacyNoticeRegion.LV]: "Latvia",
    [PrivacyNoticeRegion.VA]: "Vatican City",
    [PrivacyNoticeRegion.AT]: "Austria",
    [PrivacyNoticeRegion.AL]: "Albania",
    [PrivacyNoticeRegion.LI]: "Liechtenstein",
    [PrivacyNoticeRegion.GR]: "Greece",
    [PrivacyNoticeRegion.IT]: "Italy",
    [PrivacyNoticeRegion.AD]: "Andorra",
    [PrivacyNoticeRegion.GB]: "United Kingdom",
    [PrivacyNoticeRegion.RU]: "Russia",
    [PrivacyNoticeRegion.SI]: "Slovenia",
    [PrivacyNoticeRegion.BY]: "Belarus",
    [PrivacyNoticeRegion.CH]: "Switzerland",
    [PrivacyNoticeRegion.HU]: "Hungary",
    [PrivacyNoticeRegion.BG]: "Bulgaria",
    [PrivacyNoticeRegion.HR]: "Croatia",
    [PrivacyNoticeRegion.TC]: "Turks and Caicos Islands",
    [PrivacyNoticeRegion.CW]: "Curaçao",
    [PrivacyNoticeRegion.GP]: "Guadeloupe",
    [PrivacyNoticeRegion.UM]: "United States Minor Outlying Islands",
    [PrivacyNoticeRegion.GT]: "Guatemala",
    [PrivacyNoticeRegion.PM]: "Saint Pierre and Miquelon",
    [PrivacyNoticeRegion.BQ]: "Caribbean Netherlands",
    [PrivacyNoticeRegion.GL]: "Greenland",
    [PrivacyNoticeRegion.SX]: "Sint Maarten",
    [PrivacyNoticeRegion.PA]: "Panama",
    [PrivacyNoticeRegion.AW]: "Aruba",
    [PrivacyNoticeRegion.MQ]: "Martinique",
    [PrivacyNoticeRegion.AG]: "Antigua and Barbuda",
    [PrivacyNoticeRegion.BM]: "Bermuda",
    [PrivacyNoticeRegion.CU]: "Cuba",
    [PrivacyNoticeRegion.GD]: "Grenada",
    [PrivacyNoticeRegion.NI]: "Nicaragua",
    [PrivacyNoticeRegion.LC]: "Saint Lucia",
    [PrivacyNoticeRegion.KN]: "Saint Kitts and Nevis",
    [PrivacyNoticeRegion.DO]: "Dominican Republic",
    [PrivacyNoticeRegion.VC]: "Saint Vincent and the Grenadines",
    [PrivacyNoticeRegion.BZ]: "Belize",
    [PrivacyNoticeRegion.HT]: "Haiti",
    [PrivacyNoticeRegion.JM]: "Jamaica",
    [PrivacyNoticeRegion.BS]: "Bahamas",
    [PrivacyNoticeRegion.MX]: "Mexico",
    [PrivacyNoticeRegion.MF]: "Saint Martin",
    [PrivacyNoticeRegion.SV]: "El Salvador",
    [PrivacyNoticeRegion.BL]: "Saint Barthélemy",
    [PrivacyNoticeRegion.AI]: "Anguilla",
    [PrivacyNoticeRegion.MS]: "Montserrat",
    [PrivacyNoticeRegion.VG]: "British Virgin Islands",
    [PrivacyNoticeRegion.BB]: "Barbados",
    [PrivacyNoticeRegion.HN]: "Honduras",
    [PrivacyNoticeRegion.KY]: "Cayman Islands",
    [PrivacyNoticeRegion.DM]: "Dominica",
    [PrivacyNoticeRegion.TT]: "Trinidad and Tobago",
    [PrivacyNoticeRegion.CR]: "Costa Rica",
    [PrivacyNoticeRegion.SR]: "Suriname",
    [PrivacyNoticeRegion.CX]: "Christmas Island",
    [PrivacyNoticeRegion.WS]: "Samoa",
    [PrivacyNoticeRegion.PF]: "French Polynesia",
    [PrivacyNoticeRegion.AS]: "American Samoa",
    [PrivacyNoticeRegion.NC]: "New Caledonia",
    [PrivacyNoticeRegion.TK]: "Tokelau",
    [PrivacyNoticeRegion.PW]: "Palau",
    [PrivacyNoticeRegion.KI]: "Kiribati",
    [PrivacyNoticeRegion.VU]: "Vanuatu",
    [PrivacyNoticeRegion.PN]: "Pitcairn Islands",
    [PrivacyNoticeRegion.CK]: "Cook Islands",
    [PrivacyNoticeRegion.FJ]: "Fiji",
    [PrivacyNoticeRegion.PG]: "Papua New Guinea",
    [PrivacyNoticeRegion.MP]: "Northern Mariana Islands",
    [PrivacyNoticeRegion.NU]: "Niue",
    [PrivacyNoticeRegion.TV]: "Tuvalu",
    [PrivacyNoticeRegion.NF]: "Norfolk Island",
    [PrivacyNoticeRegion.TO]: "Tonga",
    [PrivacyNoticeRegion.FM]: "Micronesia",
    [PrivacyNoticeRegion.SB]: "Solomon Islands",
    [PrivacyNoticeRegion.NR]: "Nauru",
    [PrivacyNoticeRegion.WF]: "Wallis and Futuna",
    [PrivacyNoticeRegion.GU]: "Guam",
    [PrivacyNoticeRegion.AU]: "Australia",
    [PrivacyNoticeRegion.NZ]: "New Zealand",
    [PrivacyNoticeRegion.MH]: "Marshall Islands",
    [PrivacyNoticeRegion.CC]: "Cocos (Keeling) Islands",
    [PrivacyNoticeRegion.VE]: "Venezuela",
    [PrivacyNoticeRegion.PY]: "Paraguay",
    [PrivacyNoticeRegion.BR]: "Brazil",
    [PrivacyNoticeRegion.CO]: "Colombia",
    [PrivacyNoticeRegion.PE]: "Peru",
    [PrivacyNoticeRegion.CL]: "Chile",
    [PrivacyNoticeRegion.UY]: "Uruguay",
    [PrivacyNoticeRegion.AR]: "Argentina",
    [PrivacyNoticeRegion.GY]: "Guyana",
    [PrivacyNoticeRegion.BO]: "Bolivia",
    [PrivacyNoticeRegion.GF]: "French Guiana",
    [PrivacyNoticeRegion.EC]: "Ecuador",
    [PrivacyNoticeRegion.FK]: "Falkland Islands",
    [PrivacyNoticeRegion.US_AL]: "Alabama",
    [PrivacyNoticeRegion.US_AK]: "Alaska",
    [PrivacyNoticeRegion.US_AZ]: "Arizona",
    [PrivacyNoticeRegion.US_AR]: "Arkansas",
    [PrivacyNoticeRegion.US_CA]: "California",
    [PrivacyNoticeRegion.US_CO]: "Colorado",
    [PrivacyNoticeRegion.US_CT]: "Connecticut",
    [PrivacyNoticeRegion.US_DE]: "Delaware",
    [PrivacyNoticeRegion.US_DC]: "District of Columbia (DC)",
    [PrivacyNoticeRegion.US_FL]: "Florida",
    [PrivacyNoticeRegion.US_GA]: "Georgia",
    [PrivacyNoticeRegion.US_HI]: "Hawaii",
    [PrivacyNoticeRegion.US_ID]: "Idaho",
    [PrivacyNoticeRegion.US_IL]: "Illinois",
    [PrivacyNoticeRegion.US_IN]: "Indiana",
    [PrivacyNoticeRegion.US_IA]: "Iowa",
    [PrivacyNoticeRegion.US_KS]: "Kansas",
    [PrivacyNoticeRegion.US_KY]: "Kentucky",
    [PrivacyNoticeRegion.US_LA]: "Louisiana",
    [PrivacyNoticeRegion.US_ME]: "Maine",
    [PrivacyNoticeRegion.US_MD]: "Maryland",
    [PrivacyNoticeRegion.US_MA]: "Massachusetts",
    [PrivacyNoticeRegion.US_MI]: "Michigan",
    [PrivacyNoticeRegion.US_MN]: "Minnesota",
    [PrivacyNoticeRegion.US_MS]: "Mississippi",
    [PrivacyNoticeRegion.US_MO]: "Missouri",
    [PrivacyNoticeRegion.US_MT]: "Montana",
    [PrivacyNoticeRegion.US_NE]: "Nebraska",
    [PrivacyNoticeRegion.US_NV]: "Nevada",
    [PrivacyNoticeRegion.US_NH]: "New Hampshire",
    [PrivacyNoticeRegion.US_NJ]: "New Jersey",
    [PrivacyNoticeRegion.US_NM]: "New Mexico",
    [PrivacyNoticeRegion.US_NY]: "New York",
    [PrivacyNoticeRegion.US_NC]: "North Carolina",
    [PrivacyNoticeRegion.US_ND]: "North Dakota",
    [PrivacyNoticeRegion.US_OH]: "Ohio",
    [PrivacyNoticeRegion.US_OK]: "Oklahoma",
    [PrivacyNoticeRegion.US_OR]: "Oregon",
    [PrivacyNoticeRegion.US_PA]: "Pennsylvania",
    [PrivacyNoticeRegion.US_PR]: "Puerto Rico",
    [PrivacyNoticeRegion.US_RI]: "Rhode Island",
    [PrivacyNoticeRegion.US_SC]: "South Carolina",
    [PrivacyNoticeRegion.US_SD]: "San Diego",
    [PrivacyNoticeRegion.US_TN]: "Tennessee",
    [PrivacyNoticeRegion.US_TX]: "Texas",
    [PrivacyNoticeRegion.US_UT]: "Utah",
    [PrivacyNoticeRegion.US_VA]: "Virginia",
    [PrivacyNoticeRegion.US_VI]: "United States Virgin Islands",
    [PrivacyNoticeRegion.US_VT]: "Vermon",
    [PrivacyNoticeRegion.US_WA]: "Washington",
    [PrivacyNoticeRegion.US_WV]: "West Virginia",
    [PrivacyNoticeRegion.US_WI]: "Wisconsin",
    [PrivacyNoticeRegion.US_WY]: "Wyoming",
    [PrivacyNoticeRegion.CA_AB]: "Alberta",
    [PrivacyNoticeRegion.CA_BC]: "British Columbia",
    [PrivacyNoticeRegion.CA_MB]: "Manitoba",
    [PrivacyNoticeRegion.CA_NB]: "New Brunswick",
    [PrivacyNoticeRegion.CA_NL]: "Newfoundland and Labrador",
    [PrivacyNoticeRegion.CA_NS]: "Nova Scotia",
    [PrivacyNoticeRegion.CA_ON]: "Ontario",
    [PrivacyNoticeRegion.CA_PE]: "Prince Edward Island",
    [PrivacyNoticeRegion.CA_QC]: "Quebec",
    [PrivacyNoticeRegion.CA_SK]: "Saskatchewan",
    [PrivacyNoticeRegion.CA_NT]: "Northwest Territories",
    [PrivacyNoticeRegion.CA_NU]: "Nunavut",
    [PrivacyNoticeRegion.CA_YT]: "Yukon",
    [PrivacyNoticeRegion.CA]: "Canada",
    [PrivacyNoticeRegion.US]: "United States",
    [PrivacyNoticeRegion.MEXICO_CENTRAL_AMERICA]: "Mexico and Central America",
    [PrivacyNoticeRegion.CARIBBEAN]: "Caribbean",
    [PrivacyNoticeRegion.EEA]: "European Economic Area (EEA)",
    [PrivacyNoticeRegion.NON_EEA]: "Non European Economic Area",
  };

export const PRIVACY_NOTICE_REGION_MAP = new Map(
  Object.entries(PRIVACY_NOTICE_REGION_RECORD)
);

export const PRIVACY_NOTICE_REGION_OPTIONS = Object.entries(
  PRIVACY_NOTICE_REGION_RECORD
).map((entry) => ({
  value: entry[0],
  label: entry[1],
}));
