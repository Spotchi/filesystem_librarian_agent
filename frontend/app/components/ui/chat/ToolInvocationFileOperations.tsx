import React from 'react';
import { FaArrowRight, FaTrash, FaEdit } from 'react-icons/fa';

interface FileOperation {
  operationType: 'move' | 'delete' | 'rename';
  sourcePath: string;
  destinationPath?: string;
}

interface FileOperationsSuggestion {
  operations: FileOperation[];
}

interface ToolInvocationFileOperationsProps {
  args: {
    suggestion: FileOperationsSuggestion;
  };
}

const ToolInvocationFileOperations: React.FC<ToolInvocationFileOperationsProps> = ({ args }) => {
  const getOperationIcon = (type: string) => {
    switch (type) {
      case 'move':
        return <FaArrowRight className="text-blue-400" />;
      case 'delete':
        return <FaTrash className="text-red-400" />;
      case 'rename':
        return <FaEdit className="text-green-400" />;
      default:
        return null;
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg p-4 space-y-3">
      <h3 className="text-white text-lg font-semibold mb-4">File Operations</h3>
      {args.suggestion.operations.map((operation, index) => (
        <div
          key={index}
          className="flex items-center space-x-3 bg-gray-700 p-3 rounded-md text-gray-200"
        >
          <span className="flex-shrink-0">
            {getOperationIcon(operation.operationType)}
          </span>
          <div className="flex-1 overflow-hidden">
            <div className="flex items-center space-x-2">
              <span className="text-gray-400 font-mono text-sm truncate">
                {operation.sourcePath}
              </span>
              {operation.destinationPath && (
                <>
                  <FaArrowRight className="text-gray-500 flex-shrink-0" />
                  <span className="text-gray-400 font-mono text-sm truncate">
                    {operation.destinationPath}
                  </span>
                </>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default ToolInvocationFileOperations; 