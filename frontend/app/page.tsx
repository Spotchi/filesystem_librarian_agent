'use client';

import Header from "@/app/components/header";
import ChatSection from "./components/chat-section";
import DirectoryList from "./components/directory-list";
import { useRef } from "react";
import type { ChatSectionRef } from "./components/chat-section";
import { useAuth } from './providers/auth-provider';

export default function Home() {
  const chatSectionRef = useRef<ChatSectionRef>(null);
  const { loading } = useAuth();

  if (loading) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center p-24 background-gradient">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen flex-col items-center gap-10 p-24 background-gradient">
      <Header />
      <div className="flex w-full gap-8">
        <div className="flex-1">
          <ChatSection ref={chatSectionRef} />
        </div>
        {/* <div className="w-64">
          <DirectoryList chatSectionRef={chatSectionRef} />
        </div> */}
      </div>
    </main>
  );
}
