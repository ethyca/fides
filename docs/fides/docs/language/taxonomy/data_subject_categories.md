# Data Subject Categories Reference

Data Subject Categories are the group of labels commonly assigned to describe the type of system users to whom data may belong or is being processed. Examples might be customers, patients or simply abstract users.

!!! Note "Extensibility and Interopability"
    Data Subject Categories in Fides are designed to support common privacy regulations and standards out of the box, these include GDPR, CCPA, LGPD and ISO 19944. 
    
    You can extend the taxonomy to support your organization's needs. If you do this, we recommend extending from the existing categories to ensure interopability inside and outside your organization.

    If you have suggestions for core categories that should ship with the taxonomy, please submit your requests [here](https://github.com/ethyca/fides/issues)


## Data Subject Classes

At present, Data Subjects are a flat structure with no subclassifications, although this is likely to change over time.

| Label                                          | Parent Key                 | Description                                                                                               |
| ---                                            | ---                        | ---                                                                                                       |
|`anonymous_user` |`-`       |An individual that is unidentifiable to the systems. Note - This should only be applied to truly anonymous users where there is no risk of re-identification|
|`citizen_voter`  |`-`       |An individual registered to voter with a state or authority.                                                                                                |
|`commuter`       |`-`       |An individual that is traveling or transiting in the context of location tracking.                                                                          |
|`consultant`     |`-`       |An individual employed in a consultative/temporary capacity by the organization.                                                                            |
|`customer`       |`-`       |An individual or other organization that purchases goods or services from the organization.                                                                 |
|`employee`       |`-`       |An individual employed by the organization.                                                                                                                 |
|`job_applicant`  |`-`       |An individual applying for employment to the organization.                                                                                                  |
|`next_of_kin`    |`-`       |A relative of any other individual subject where such a relationship is known.                                                                              |
|`passenger`      |`-`       |An individual traveling on some means of provided transport.                                                                                                |
|`patient`        |`-`       |An individual identified for the purposes of any medical care.                                                                                              |
|`prospect`       |`-`       |An individual or organization to whom an organization is selling goods or services.                                                                         |
|`shareholder`    |`-`       |An individual or organization that holds equity in the organization.                                                                                        |
|`supplier_vendor`|`-`       |An individual or organization that provides services or goods to the organization.                                                                          |
|`trainee`        |`-`       |An individual undergoing training by the organization.                                                                                                      |
|`visitor`        |`-`       |An individual visiting a location.                                                                                                                          |
