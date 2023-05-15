from pydantic import BaseModel, Field


class DiscoveryResponse(BaseModel):
    ram: float = Field(
        default=0.0,
        description='All available RAM in bytes'
    )
    cpu_cores: int = Field(
        default=0,
        description='Number of available CPU cores'
    )
    has_cuda: bool = Field(
        default=False,
        description="Whether deployment supports NVIDIA's CUDA"
    )
    cuda_version: str = Field(
        default='Cuda version not detected',
        description='Major/minor version of CUDA'
    )
    has_ocrd_all: bool = Field(
        default=False,
        description='Whether deployment is based on ocrd_all'
    )
    ocrd_all_version: str = Field(
        default='Ocrd all version not detected',
        description='Git tag of the ocrd_all version implemented'
    )
    has_docker: bool = Field(
        default=False,
        description='Whether the OCR-D executables run in a Docker container'
    )
