import AgentList from '../components/AgentList';

export default function AgentsPage() {
  // You can set the baseUrl to your backend API endpoint
  const baseUrl = '';
  return (
    <main class="max-w-2xl mx-auto mt-8">
      <AgentList baseUrl={baseUrl} />
    </main>
  );
}
