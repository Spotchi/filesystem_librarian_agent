from typing import List, Optional
from pydantic import BaseModel


class FileOperation(BaseModel):
    """A single file or folder operation to be performed"""
    operationType: str  # Literal["move", "rename"] - if using Python 3.8+, you can use Literal
    sourcePath: str
    destinationPath: str
    isDirectory: bool = False
    description: Optional[str] = None

    # class Config:
    #     json_schema_extra = {
    #         "description": "Type of operation to perform",
    #         "operationType": {
    #             "enum": ["move", "rename"]
    #         }
    #     }


class FileOperationsResponse(BaseModel):
    """Schema for a list of file and folder operations"""
    operations: List[FileOperation]
    batchId: Optional[str] = None
    dryRun: bool = False

    # class Config:
    #     json_schema_extra = {
    #         "title": "File Operations Schema",
    #         "description": "Schema for a list of file and folder operations"
    #     }
    
if __name__ == '__main__':
    print(FileOperationsResponse.model_json_schema())