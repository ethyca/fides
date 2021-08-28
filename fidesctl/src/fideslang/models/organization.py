from fideslang.models.fides_model import FidesModel


class Organization(FidesModel):
    # It inherits this from FidesModel but Organization's don't have this field
    organiztionId: None = None
