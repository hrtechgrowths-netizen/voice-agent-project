import { Dashboard } from './pages/Dashboard';

function App() {
  return (
    <Dashboard
      token="guest"
      onLogout={() => {}}
    />
  );
}

export default App;