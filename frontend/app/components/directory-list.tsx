'use client';

import type { ChatSectionRef } from './chat-section';

interface DirectoryListProps {
  chatSectionRef: React.RefObject<ChatSectionRef>;
}

const DirectoryList = ({ chatSectionRef }: DirectoryListProps) => {
  const directories = process.env.INPUT_FILES?.split(',') || [];
  console.log(process.env.INPUT_FILES);
  console.log(directories);

  const handleDirectoryClick = (dir: string) => {
    const decodedDir = decodeURIComponent(dir.trim());
    console.log(decodedDir);
    chatSectionRef.current?.setInput(`Reorganize ${decodedDir}`);
  };

  return (
    <div className="bg-white/10 backdrop-blur-md rounded-lg p-4">
      <h2 className="text-xl font-semibold mb-4">Directories</h2>
      <ul className="space-y-2">
        {directories.map((dir, index) => (
          <li 
            key={index} 
            className="border rounded-lg p-3 hover:bg-white/5 cursor-pointer transition-colors"
            onClick={() => handleDirectoryClick(dir)}
          >
            <div className="flex items-center gap-2">
              <h3 className="font-medium">
                {decodeURIComponent(dir.trim()).split('/').pop()}
              </h3>
              <div className="relative group">
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div className="absolute left-0 bottom-full mb-2 hidden group-hover:block">
                  <div className="bg-gray-900 text-white text-sm rounded p-2 whitespace-nowrap">
                    {decodeURIComponent(dir.trim())}
                  </div>
                </div>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default DirectoryList; 