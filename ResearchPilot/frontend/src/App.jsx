import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import ResearchInput from './pages/ResearchInput';
import TaskBoard from './pages/TaskBoard';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<ResearchInput />} />
          <Route path="tasks" element={<TaskBoard />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
