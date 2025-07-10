import type { Component } from 'solid-js';

const App: Component = () => {
  return (
    <div class="min-h-screen bg-gray-900 text-white flex items-center justify-center">
      <div class="text-center">
        <h1 class="text-4xl font-bold mb-4">🌊 OMNIMESH Control Panel</h1>
        <p class="text-xl">Next-generation agent orchestration interface</p>
        <div class="mt-8">
          <button class="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg">
            Initialize System
          </button>
        </div>
      </div>
    </div>
  );
};

export default App;
