import axios from "axios";
import { create } from "zustand";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

let indexPollTimer = null;

const sleep = (ms) => new Promise((resolve) => window.setTimeout(resolve, ms));

const splitForStreaming = (text) => text.match(/\s+|\S+/g) ?? [text];

const buildChatHistory = (messages) =>
  messages
    .filter((message) => {
      const content = message.content?.trim();
      return content && !(message.role === "ai" && content === "Lorebait is ready.");
    })
    .slice(-8)
    .map((message) => ({
      role: message.role === "ai" ? "assistant" : message.role,
      content: message.content.slice(0, 2000),
    }));

const progressForStatus = (status, previousProgress) => {
  const normalized = status?.toLowerCase() ?? "queued";
  const floorByStatus = {
    queued: 12,
    scanning: 26,
    tokenizing: 48,
    indexing: 62,
    embedding: 76,
    completed: 100,
    failed: previousProgress,
  };

  const floor = floorByStatus[normalized] ?? 38;
  if (normalized === "completed") return 100;
  return Math.min(92, Math.max(floor, previousProgress + 4));
};

const appendToLastAiMessage = (set, addition) => {
  set((state) => {
    const messages = [...state.messages];
    const lastMessage = messages[messages.length - 1];

    if (!lastMessage || lastMessage.role !== "ai") {
      messages.push({ role: "ai", content: addition });
    } else {
      messages[messages.length - 1] = {
        ...lastMessage,
        content: `${lastMessage.content}${addition}`,
      };
    }

    return { messages };
  });
};

export const useLorebaitStore = create((set, get) => ({
  activeFolder: "",
  activePersona: "tutor",
  messages: [
    {
      role: "ai",
      content: "Lorebait is ready.",
    },
  ],
  isIndexing: false,
  indexingStatus: "idle",
  indexingProgress: 0,
  indexingError: null,
  isStreaming: false,
  streamError: null,

  setActiveFolder: (activeFolder) => set({ activeFolder }),
  setActivePersona: (activePersona) => set({ activePersona }),

  loadSession: async () => {
    try {
      const { data } = await api.get("/session");
      set({
        activeFolder: data.active_folder ?? "",
        activePersona: data.active_persona ?? "tutor",
      });
    } catch (error) {
      console.warn("Unable to load Lorebait session", error);
    }
  },

  resetChat: () =>
    set({
      messages: [],
      streamError: null,
    }),

  beginIndexPolling: (folderPath) => {
    if (indexPollTimer) {
      window.clearInterval(indexPollTimer);
    }

    const poll = async () => {
      try {
        const { data } = await api.get("/index/status", {
          params: { directory_path: folderPath },
        });

        const status = data.status ?? "queued";
        const failed = status === "failed";
        const completed = status === "completed";

        set((state) => ({
          indexingStatus: status,
          indexingProgress: progressForStatus(status, state.indexingProgress),
          isIndexing: !failed && !completed,
          indexingError: failed ? data.last_error ?? "Indexing failed." : null,
        }));

        if (failed || completed) {
          window.clearInterval(indexPollTimer);
          indexPollTimer = null;
        }
      } catch (error) {
        console.warn("Unable to poll indexing status", error);
        set((state) => ({
          indexingProgress: Math.min(88, state.indexingProgress + 2),
        }));
      }
    };

    indexPollTimer = window.setInterval(poll, 1600);
    poll();
  },

  indexFolder: async () => {
    const folderPath = get().activeFolder.trim();
    if (!folderPath) {
      set({
        indexingStatus: "idle",
        indexingError: "Enter a local directory path before indexing.",
      });
      return;
    }

    set({
      isIndexing: true,
      indexingStatus: "queued",
      indexingProgress: 8,
      indexingError: null,
    });

    try {
      await api.post("/index", { directory_path: folderPath });
      get().beginIndexPolling(folderPath);
    } catch (error) {
      const detail = error.response?.data?.detail;
      set({
        isIndexing: false,
        indexingStatus: "failed",
        indexingError: typeof detail === "string" ? detail : "Could not start indexing.",
      });
    }
  },

  sendMessage: async (content) => {
    const message = content.trim();
    if (!message || get().isStreaming) return;

    const { activeFolder, activePersona, messages } = get();
    const history = buildChatHistory(messages);

    set((state) => ({
      messages: [
        ...state.messages,
        { role: "user", content: message },
        { role: "ai", content: "" },
      ],
      isStreaming: true,
      streamError: null,
    }));

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          persona: activePersona,
          folder_path: activeFolder || null,
          top_k: 6,
          history,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || `Chat failed with ${response.status}`);
      }

      if (!response.body) {
        throw new Error("The browser did not expose a readable response stream.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        for (const token of splitForStreaming(chunk)) {
          appendToLastAiMessage(set, token);
          if (token.trim()) {
            await sleep(16);
          }
        }
      }

      const finalChunk = decoder.decode();
      if (finalChunk) {
        appendToLastAiMessage(set, finalChunk);
      }
    } catch (error) {
      const messageText =
        error instanceof Error ? error.message : "Lorebait could not stream a response.";
      set({ streamError: messageText });
      appendToLastAiMessage(set, `\n\n${messageText}`);
    } finally {
      set({ isStreaming: false });
    }
  },
}));
