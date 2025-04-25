from llama_index.core.tools import FunctionTool
from llama_index.core.workflow import Context
from app.engine.file_ops import FileOperationsResponse
import os
import shutil


async def suggest_file_operations(
    ctx: Context,
    suggestion: FileOperationsResponse,
) -> str:
    """Suggest a list of file operations to the user
    The response contains a batchId string, and an 'operations' field, each operation has a source path and a destination path, as well as an operation type (move or rename). \
    Optionally there is a isDirectory flag
    """
    return "Suggestions processed successfully"


suggestion_tool = FunctionTool.from_defaults(suggest_file_operations)

def absolute_path(path: str) -> str:
    # Append the base path to the relative path
    # If the INPUT_FILES folder name is present in the path, remove it
    parts = path.split("/")
    if parts[0] in os.environ["INPUT_FILES"]:
        parts = parts[1:]
    return os.path.join(os.environ["INPUT_FILES"], *parts)

async def apply_file_operations(
    ctx: Context,
    suggestion: FileOperationsResponse,
) -> str:
    """Apply a list of file operations to the user's directory
    """
    # suggestion = await ctx.get("suggestions")
    parsed_suggestion = FileOperationsResponse(**suggestion)
    for operation in parsed_suggestion.operations:
        if operation.isDirectory:
            print(f"Making directory: {absolute_path(operation.destinationPath)}")
            os.makedirs(absolute_path(operation.destinationPath), exist_ok=True)
        else:
            print(f"Moving file: {absolute_path(operation.sourcePath)} to {absolute_path(operation.destinationPath)}")
            shutil.move(absolute_path(operation.sourcePath), absolute_path(operation.destinationPath))
    return "File operations applied successfully"

apply_file_operations_tool = FunctionTool.from_defaults(apply_file_operations)
