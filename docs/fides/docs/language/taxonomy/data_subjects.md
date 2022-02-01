# Data Subjects Reference

A Data Subject is a label that describes a segment of  individuals whose data you store. Data Subject labels are typically fairly broad -- "Citizen", "Visitor", "Passenger", and so on -- although you be as specific as your system needs: "Fans in Section K", for example.

## Object Structure

**fides_key**<span class="required"/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_constrained string_

A string token of your own invention that uniquely identifies this Data Subject. It's your responsibility to ensure that the value is unique across all of your Data Subject objects. The value should only contain alphanumeric characters and underbars (`[A-Za-z0-9_.-]`).

**name**<span class="spacer"/>_string_

A UI-friendly label for the Data Subject.

**description**<span class="spacer"/>_string_

A human-readable description of the Data Subject.

**organization_fides_key**<span class="spacer"/>_string_<span class="spacer"/>default: `default_organization`

The fides key of the organization to which this Data Subject belongs.

!!! Note "Extensibility and Interopability"
    Data Subjects in Fides are designed to support common privacy regulations and standards out of the box, these include GDPR, CCPA, LGPD and ISO 19944.

    You can extend the taxonomy to support your organization's needs. If you do this, we recommend extending from the existing categories to ensure interopability inside and outside your organization.

    If you have suggestions for core categories that should ship with the taxonomy, please submit your requests [here](https://github.com/ethyca/fides/issues)

## Default Data Subject Types

Currently, your collection of Data Subjects is given as a flat list: A Data Subject can't contain other Data Subjects.

| Label                                          | Parent Key                 | Description                                                                                               |
| ---                                            | ---                        | ---                                                                                                       |
|`anonymous_user` |`-`       |An individual who is unidentifiable to the systems. Note - This should only be applied to truly anonymous users where there is no risk of re-identification|
|`citizen_voter`  |`-`       |An individual registered to voter with a state or authority.                                                                                                |
|`commuter`       |`-`       |An individual who is traveling or transiting in the context of location tracking.                                                                          |
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
