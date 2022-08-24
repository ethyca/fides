from fides.api.ops.schemas.masking.masking_configuration import FormatPreservationConfig


class FormatPreservation:
    """currently supports fixed suffix formats only, such as email address"""

    def __init__(self, config: FormatPreservationConfig):
        self.suffix = config.suffix

    def format(self, value: str) -> str:
        return value + self.suffix
