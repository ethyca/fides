# Data Identification Qualifiers Reference

Data Identification Qualifiers describe the degree of identification of the given data. 

!!! Note "Extensibility and Interopability"
    Data Identification Qualifiers in Fides are designed to support common privacy regulations and standards out of the box, these include GDPR, CCPA, LGPD and ISO 19944. 
    
    You can extend the taxonomy to support your system needs. If you do this, we recommend extending from the existing class structures to ensure interopability inside and outside your organization.

    If you have suggestions for core classes that should ship with the taxonomy, please submit your requests here (**needs link to feature requests**).


## Data Identification Qualifiers

At present, Data Identification Qualifiers are a flat structure with no subclassifications.

| Label                       | Parent Key                 | Description                                                                                                                                                                                    |
| ---                         | ---                        | ---                                                                                                                                                                                            |
|`identified_data`            |`-`       |Data that directly identifies an individual.                                                                                                                                                                      |
|`pseudonymized_data`         |`-`       |Data for which all identifiers have been substituted with unrelated values, rendering the individual unidentifiable and cannot be reasonably reversed other than by the party that performed the pseudonymization.|
|`unlinked_pseudonymized_data`|`-`       |Data for which all identifiers have been substituted with unrelated values and linkages broken such that it may not be reversed, even by the party that performed the pseudonymization.                           |
|`anonymized_data`            |`-`       |Data where all attributes have been sufficiently altered that the individaul cannot be reidentified by this data or in combination with other datasets.                                                           |
|`aggregated_data`            |`-`       |Statistical data that does not contain individually identifying information but includes information about groups of individuals that renders individual identification impossible.                               |

