import AgentList from '../components/AgentList';

export default function AgentsPage() {
  // Backend API endpoint from environment or fallback
  const baseUrl = import.meta.env['VITE_API_BASE_URL'] || 'http://localhost:8080';
  return (
    <main class="max-w-2xl mx-auto mt-8">
      <AgentList baseUrl={baseUrl} />
    </main>
  );
}
