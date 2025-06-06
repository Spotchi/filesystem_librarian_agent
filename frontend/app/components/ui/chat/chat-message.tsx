import { Check, Copy } from "lucide-react";

import { JSONValue, Message, ToolCall } from "ai";
import Image from "next/image";
import { Button } from "../button";
import ChatAvatar from "./chat-avatar";
import Markdown from "./markdown";
import { useCopyToClipboard } from "./use-copy-to-clipboard";
import ToolInvocationFileOperations from "./ToolInvocationFileOperations";
import { CodeBlock } from "./codeblock";

interface ChatMessageImageData {
  type: "image_url";
  image_url: {
    url: string;
  };
}

// This component will parse message data and render the appropriate UI.
function ChatMessageData({ messageData }: { messageData: JSONValue }) {
  const { image_url, type } = messageData as unknown as ChatMessageImageData;
  if (type === "image_url") {
    return (
      <div className="rounded-md max-w-[200px] shadow-md">
        <Image
          src={image_url.url}
          width={0}
          height={0}
          sizes="100vw"
          style={{ width: "100%", height: "auto" }}
          alt=""
        />
      </div>
    );
  }
  return null;
}

export default function ChatMessage(chatMessage: Message) {
  const { isCopied, copyToClipboard } = useCopyToClipboard({ timeout: 2000 });
  return (
    <div className="flex items-start gap-4 pr-5 pt-5">
      <ChatAvatar role={chatMessage.role} />
      <div className="group flex flex-1 justify-between gap-2">
        <div className="flex-1 space-y-4">
        {chatMessage.parts && (chatMessage.parts as any[]).map((part, i) => {
            switch (part.type) {
              case 'text':
                return null;
              case 'tool-invocation': {
                const components = [];
                
                // Add appropriate tool invocation component based on tool name
                if (part.toolInvocation.toolName === 'suggest_file_operations' || 
                    part.toolInvocation.toolName === 'apply_file_operations') {
                  components.push(
                    <ToolInvocationFileOperations 
                      key={`${chatMessage.id}-${i}-tool`}
                      args={part.toolInvocation.args} 
                    />
                  );
                } else if (part.toolInvocation.toolName === 'get_vault_tree') {
                  // No component needed
                } else {
                  components.push(
                    <div key={`${chatMessage.id}-${i}-tool`}>
                      {JSON.stringify(part.toolInvocation)}
                    </div>
                  );
                }

                // Add result div if state is result
                if (part.toolInvocation.state === 'result') {
                  const resultContent = part.toolInvocation.result.content;
                  const status = part.toolInvocation.result.is_error == false ? "success" : "error";
                  components.push(
                    <div 
                      key={`${chatMessage.id}-${i}-result`} 
                      className={`${status === "error" ? "bg-red-100" : "bg-green-100"} p-2 rounded`}
                    >
                      {status}
                      <CodeBlock
                        // key={Math.random()}
                        language=""
                        value={resultContent}
                      />
                    </div>
                  );
                }

                return components.length > 0 ? <>{components}</> : null;
              }
              default:
                return <div key={`${chatMessage.id}-${i}`}>{JSON.stringify(part)}</div>;
            }
          })}
          {chatMessage.data && (
            <ChatMessageData messageData={chatMessage.data} />
          )}
          <Markdown content={chatMessage.content} />
          
        </div>
        <Button
          onClick={() => copyToClipboard(chatMessage.content)}
          size="icon"
          variant="ghost"
          className="h-8 w-8 opacity-0 group-hover:opacity-100"
        >
          {isCopied ? (
            <Check className="h-4 w-4" />
          ) : (
            <Copy className="h-4 w-4" />
          )}
        </Button>
      </div>
    </div>
  );
}
