from typing_extensions import NotRequired
from typing import TypedDict, Dict, TypeAlias, Union, Literal

Ec2InstanceSize: TypeAlias = Union[
    Literal["micro"],
    Literal["small"],
    Literal["medium"],
    Literal["large"],
    Literal["xlarge"],
    Literal["2xlarge"],
    Literal["4xlarge"],
    Literal["8xlarge"],
]


class Ec2InstanceOptions(TypedDict, total=True):
    description: str
    instance_size: Ec2InstanceSize
    name: NotRequired[str]
    tags: NotRequired[Dict[str, str]]
