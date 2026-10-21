import { Routes, Route } from 'react-router-dom';
import { LiveGuardPage } from '@pages/LiveGuard';
import { TestLabPage } from '@pages/TestLab';
import { SetupPage } from '@pages/Setup';
import { AboutPage } from '@pages/About';
import { Layout } from '@components/Layout';

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<LiveGuardPage />} />
        <Route path="/test" element={<TestLabPage />} />
        <Route path="/setup" element={<SetupPage />} />
        <Route path="/about" element={<AboutPage />} />
      </Routes>
    </Layout>
  );
}

export default App;