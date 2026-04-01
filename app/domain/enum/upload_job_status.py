from enum import StrEnum, unique


@unique
class UploadJobStatus(StrEnum):
    INITIALIZED = "initialized"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
