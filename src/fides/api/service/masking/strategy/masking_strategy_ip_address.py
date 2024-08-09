import ipaddress
from typing import List, Optional, Type

from fides.api.schemas.masking.masking_configuration import (
    IPMaskingConfiguration,
)
from fides.api.schemas.masking.masking_strategy_description import (
    MaskingStrategyConfigurationDescription,
    MaskingStrategyDescription,
)
from fides.api.service.masking.strategy.format_preservation import FormatPreservation
from fides.api.service.masking.strategy.masking_strategy import MaskingStrategy


class IPMaskingStrategy(MaskingStrategy):
    """Masks the values with a pre-determined value"""

    name = "ip_mask"
    configuration_model = IPMaskingConfiguration

    def __init__(
        self,
        configuration: IPMaskingConfiguration,
    ):
        pass

    def mask(
        self, values: Optional[List[str]], request_id: Optional[str]
    ) -> Optional[List[str]]:
        """Replaces the value with the value specified in strategy spec. Returns None if input is
        None"""
        if values is None:
            return None
        masked_values: List[str] = []
        for val in values:
            anonymized_ip = anonymize_ip_address(val)
            masked_values.append(anonymized_ip) if anonymized_ip else masked_values.append(val)
        return masked_values

    def secrets_required(self) -> bool:
        return False

    @classmethod
    def get_description(cls: Type[MaskingStrategy]) -> MaskingStrategyDescription:
        return MaskingStrategyDescription(
            name=cls.name,
            description="Masks the last octet of an ip",
            configurations=[
            ],
        )

    @staticmethod
    def data_type_supported(data_type: Optional[str]) -> bool:
        """Determines whether or not the given data type is supported by this masking strategy"""
        supported_data_types = {"string"}
        return data_type in supported_data_types


def anonymize_ip_address(ip_address: Optional[str]) -> Optional[str]:
    """Mask IP Address
    - For ipv4, set last octet to 0
    - For ipv6, set last 80 of the 128 bits are set to zero.
    """
    if not ip_address:
        return None

    try:
        ip_object = ipaddress.ip_address(ip_address)

        if ip_object.version == 4:
            ipv4_network = ipaddress.IPv4Network(ip_address + "/24", strict=False)
            masked_ip_address = str(ipv4_network.network_address)
            return masked_ip_address.split("/", maxsplit=1)[0]

        if ip_object.version == 6:
            ipv6_network = ipaddress.IPv6Network(ip_address + "/48", strict=False)
            return str(ipv6_network.network_address.exploded)

        return None

    except ValueError:
        return None