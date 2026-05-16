import { useEffect } from "react";
import {
  AlertTriangle,
  BookOpenCheck,
  Brain,
  CheckCircle2,
  DatabaseZap,
  FolderOpen,
  GraduationCap,
  Loader2,
  Microscope,
} from "lucide-react";

import ChatWindow from "./components/ChatWindow.jsx";
import { useLorebaitStore } from "./store.js";

const personas = [
  {
    id: "tutor",
    label: "Tutor",
    description: "Explains concepts and closes with a quiz.",
    icon: GraduationCap,
    accent: "text-teal-200 border-teal-400/40 bg-teal-400/10",
  },
  {
    id: "researcher",
    label: "Researcher",
    description: "Synthesizes notes with filename citations.",
    icon: Microscope,
    accent: "text-sky-200 border-sky-400/40 bg-sky-400/10",
  },
  {
    id: "learner",
    label: "Learner",
    description: "Tests recall through pointed questions.",
    icon: Brain,
    accent: "text-amber-200 border-amber-400/40 bg-amber-400/10",
  },
];

const statusLabel = {
  idle: "Idle",
  queued: "Queued",
  scanning: "Scanning",
  tokenizing: "Tokenizing",
  indexing: "Embedding",
  embedding: "Embedding",
  completed: "Indexed",
  failed: "Needs attention",
};

function Sidebar() {
  const activeFolder = useLorebaitStore((state) => state.activeFolder);
  const activePersona = useLorebaitStore((state) => state.activePersona);
  const isIndexing = useLorebaitStore((state) => state.isIndexing);
  const indexingStatus = useLorebaitStore((state) => state.indexingStatus);
  const indexingProgress = useLorebaitStore((state) => state.indexingProgress);
  const indexingError = useLorebaitStore((state) => state.indexingError);
  const setActiveFolder = useLorebaitStore((state) => state.setActiveFolder);
  const setActivePersona = useLorebaitStore((state) => state.setActivePersona);
  const indexFolder = useLorebaitStore((state) => state.indexFolder);

  const completed = indexingStatus === "completed";
  const failed = indexingStatus === "failed";
  const StatusIcon = failed ? AlertTriangle : completed ? CheckCircle2 : isIndexing ? Loader2 : DatabaseZap;

  return (
    <aside className="flex h-full w-full flex-col border-b border-white/10 bg-slate-950/82 p-4 backdrop-blur md:w-[22rem] md:border-b-0 md:border-r md:p-5">
      <div className="flex items-center gap-3">
        <div className="grid size-11 place-items-center rounded-lg border border-teal-300/20 bg-teal-300/10 text-teal-100">
          <BookOpenCheck size={22} />
        </div>
        <div>
          <h1 className="text-lg font-extrabold tracking-normal text-slate-50">Lorebait</h1>
          <p className="font-mono text-xs text-slate-400">local learning index</p>
        </div>
      </div>

      <section className="mt-7">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-200">Active Folder</h2>
          <FolderOpen className="text-slate-500" size={17} />
        </div>
        <label className="block">
          <span className="sr-only">Local directory path</span>
          <input
            value={activeFolder}
            onChange={(event) => setActiveFolder(event.target.value)}
            placeholder="D:/notes/research"
            className="h-11 w-full rounded-md border border-white/10 bg-slate-900 px-3 font-mono text-sm text-slate-100 outline-none transition placeholder:text-slate-600 focus:border-teal-300/60 focus:ring-2 focus:ring-teal-300/15"
          />
        </label>
        <button
          type="button"
          onClick={indexFolder}
          disabled={isIndexing}
          className="mt-3 flex h-11 w-full items-center justify-center gap-2 rounded-md bg-teal-300 px-4 text-sm font-bold text-slate-950 transition hover:bg-teal-200 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
        >
          {isIndexing ? <Loader2 className="animate-spin" size={18} /> : <DatabaseZap size={18} />}
          {isIndexing ? "Indexing" : "Index Folder"}
        </button>
      </section>

      <section className="mt-6 rounded-lg border border-white/10 bg-slate-900/72 p-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold text-slate-200">Indexing Status</p>
            <p className="mt-1 font-mono text-xs text-slate-500">
              {statusLabel[indexingStatus] ?? indexingStatus}
            </p>
          </div>
          <StatusIcon
            className={`${isIndexing ? "animate-spin" : ""} ${
              failed ? "text-rose-300" : completed ? "text-teal-200" : "text-slate-400"
            }`}
            size={20}
          />
        </div>
        <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-800">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              failed ? "bg-rose-400" : "bg-teal-300"
            }`}
            style={{ width: `${indexingProgress}%` }}
          />
        </div>
        {indexingError ? <p className="mt-3 text-xs leading-5 text-rose-200">{indexingError}</p> : null}
      </section>

      <section className="mt-6">
        <h2 className="mb-3 text-sm font-semibold text-slate-200">Persona</h2>
        <div className="grid gap-3">
          {personas.map((persona) => {
            const Icon = persona.icon;
            const selected = activePersona === persona.id;

            return (
              <button
                key={persona.id}
                type="button"
                onClick={() => setActivePersona(persona.id)}
                className={`rounded-lg border p-4 text-left transition ${
                  selected
                    ? persona.accent
                    : "border-white/10 bg-slate-900/60 text-slate-300 hover:border-white/20 hover:bg-slate-900"
                }`}
              >
                <span className="flex items-center gap-3">
                  <Icon size={20} />
                  <span className="font-semibold">{persona.label}</span>
                </span>
                <span className="mt-2 block text-xs leading-5 text-slate-400">{persona.description}</span>
              </button>
            );
          })}
        </div>
      </section>
    </aside>
  );
}

export default function App() {
  const loadSession = useLorebaitStore((state) => state.loadSession);

  useEffect(() => {
    loadSession();
  }, [loadSession]);

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="flex min-h-screen flex-col md:flex-row">
        <Sidebar />
        <section className="flex min-h-0 flex-1 flex-col">
          <ChatWindow />
        </section>
      </div>
    </main>
  );
}
