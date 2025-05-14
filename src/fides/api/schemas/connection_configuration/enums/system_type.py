from enum import Enum


class SystemType(Enum):
    data_catalog = "data_catalog"
    database = "database"
    email = "email"
    manual = "manual"
    saas = "saas"
    system = "system"
    website = "website"
