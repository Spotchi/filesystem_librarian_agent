from typing import List, Optional, Literal
from pydantic import BaseModel


class FileOperation(BaseModel):
    """A single file or folder operation to be performed"""
    operationType: Literal["move", "remove"]
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