import { WorkflowChat } from "@/components/WorkflowChat";

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-50 flex flex-col items-center p-8 pb-32">
      <div className="max-w-4xl w-full space-y-4 mb-10 text-center mt-12">
        <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight">
          n8n Workflow Generator
        </h1>
        <p className="text-slate-500 text-lg max-w-2xl mx-auto">
          Describe your automation idea in natural language. Our AI Architect will design the blueprint, and the Coder will generate the ready-to-import JSON.
        </p>
      </div>

      <WorkflowChat />
    </main>
  );
}
