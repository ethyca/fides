# Enumeration: PrivacyNoticeRegion

A string that represents a specific region of the world. It is used to specify regions that apply to a [Privacy Experience](/tutorials/consent-management/consent-management-configuration/privacy-experiences#what-are-privacy-experiences).
The string is formatted with [ISO 3166](https://en.wikipedia.org/wiki/ISO_3166) two-letter codes for a country and subdivisions. They're written in lowercase and separated with an underscore. Subdivisions are currently supported for the United States and Canada.
The PrivacyNoticeRegion can also be one of the following non-iso standard codes:
- `eea` : European Economic Area
- `non_eea` : European countries that are not part of the European Economic Area
- `mexico_central_america` : Mexico and Central America
- `caribbean` : Caribbean

### Example values:
- `us` : United States
- `ca` : Canada
- `fr` : France
- `us_ca` : United States - State of California
- `us_ny` : United States - State of New York
- `ca_on` : Canada - Ontario Province
- `eea` : European Economic Area
