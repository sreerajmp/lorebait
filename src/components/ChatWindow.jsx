import { useEffect, useRef, useState } from "react";
import { Bot, Loader2, Send, UserRound } from "lucide-react";

import { useLorebaitStore } from "../store.js";

function MessageBubble({ message }) {
  const isUser = message.role === "user";

  return (
    <article className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <div className="mt-1 grid size-8 shrink-0 place-items-center rounded-md border border-teal-300/20 bg-teal-300/10 text-teal-100">
          <Bot size={17} />
        </div>
      )}
      <div
        className={`max-w-[min(46rem,88%)] rounded-lg px-4 py-3 text-sm leading-6 shadow-glow ${
          isUser
            ? "bg-slate-100 text-slate-950"
            : "border border-white/10 bg-slate-900/78 text-slate-200"
        }`}
      >
        <p className="whitespace-pre-wrap break-words">{message.content}</p>
      </div>
      {isUser && (
        <div className="mt-1 grid size-8 shrink-0 place-items-center rounded-md border border-slate-200/20 bg-slate-100 text-slate-950">
          <UserRound size={17} />
        </div>
      )}
    </article>
  );
}

export default function ChatWindow() {
  const [draft, setDraft] = useState("");
  const messages = useLorebaitStore((state) => state.messages);
  const isStreaming = useLorebaitStore((state) => state.isStreaming);
  const activePersona = useLorebaitStore((state) => state.activePersona);
  const activeFolder = useLorebaitStore((state) => state.activeFolder);
  const sendMessage = useLorebaitStore((state) => state.sendMessage);
  const resetChat = useLorebaitStore((state) => state.resetChat);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages]);

  const submitMessage = async (event) => {
    event.preventDefault();
    if (!draft.trim() || isStreaming) return;

    const nextMessage = draft;
    setDraft("");
    await sendMessage(nextMessage);
  };

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <header className="border-b border-white/10 bg-slate-950/72 px-4 py-4 backdrop-blur md:px-8">
        <div className="mx-auto flex max-w-5xl flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="font-mono text-xs uppercase text-teal-200">Lore Thread</p>
            <h2 className="mt-1 text-xl font-bold text-slate-50">Ask the indexed material</h2>
          </div>
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="rounded-md border border-white/10 bg-slate-900 px-3 py-2 font-mono text-slate-300">
              {activePersona}
            </span>
            <span className="max-w-[18rem] truncate rounded-md border border-white/10 bg-slate-900 px-3 py-2 font-mono text-slate-500">
              {activeFolder || "no folder selected"}
            </span>
            <button
              type="button"
              onClick={resetChat}
              className="rounded-md border border-white/10 px-3 py-2 text-slate-300 transition hover:border-white/20 hover:bg-slate-900"
            >
              Clear
            </button>
          </div>
        </div>
      </header>

      <div ref={scrollRef} className="min-h-0 flex-1 overflow-y-auto px-4 py-6 md:px-8">
        <div className="mx-auto flex max-w-5xl flex-col gap-5">
          {messages.length === 0 ? (
            <div className="grid min-h-[45vh] place-items-center rounded-lg border border-dashed border-white/10 bg-slate-900/35 p-8 text-center">
              <div>
                <div className="mx-auto grid size-12 place-items-center rounded-lg bg-teal-300/10 text-teal-100">
                  <Bot size={24} />
                </div>
                <p className="mt-4 text-sm text-slate-400">Your chat history is clear.</p>
              </div>
            </div>
          ) : (
            messages.map((message, index) => (
              <MessageBubble key={`${message.role}-${index}`} message={message} />
            ))
          )}
          {isStreaming && (
            <div className="flex items-center gap-2 pl-11 font-mono text-xs text-slate-500">
              <Loader2 className="animate-spin text-teal-200" size={14} />
              streaming response
            </div>
          )}
        </div>
      </div>

      <footer className="border-t border-white/10 bg-slate-950/78 px-4 py-4 backdrop-blur md:px-8">
        <form onSubmit={submitMessage} className="mx-auto flex max-w-5xl items-end gap-3">
          <label className="min-w-0 flex-1">
            <span className="sr-only">Message Lorebait</span>
            <textarea
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  submitMessage(event);
                }
              }}
              rows={1}
              placeholder="Ask about a concept, contradiction, citation, or study question..."
              className="max-h-40 min-h-12 w-full resize-none rounded-lg border border-white/10 bg-slate-900 px-4 py-3 text-sm leading-6 text-slate-100 outline-none transition placeholder:text-slate-600 focus:border-teal-300/60 focus:ring-2 focus:ring-teal-300/15"
            />
          </label>
          <button
            type="submit"
            disabled={!draft.trim() || isStreaming}
            className="grid size-12 shrink-0 place-items-center rounded-lg bg-teal-300 text-slate-950 transition hover:bg-teal-200 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
            title="Send message"
          >
            {isStreaming ? <Loader2 className="animate-spin" size={19} /> : <Send size={19} />}
          </button>
        </form>
      </footer>
    </div>
  );
}
