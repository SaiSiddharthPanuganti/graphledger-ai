import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import './styles/globals.css';
import Sidebar from './components/layout/Sidebar';
import Topbar from './components/layout/Topbar';
import Chatbot from './components/Chatbot';
import Overview from './pages/Overview';
import Reconciliation from './pages/Reconciliation';
import ITCChain from './pages/ITCChain';
import VendorRisk from './pages/VendorRisk';
import AuditTrail from './pages/AuditTrail';
import Prediction from './pages/Prediction';
import GraphExplorer from './pages/GraphExplorer';
import Traversal from './pages/Traversal';
import OCRUpload from './pages/OCRUpload';
import ITCCalculator from './pages/ITCCalculator';

const PAGE_TITLES = {
  '/': 'Executive Overview',
  '/recon': 'ITC Reconciliation',
  '/chain': 'ITC Chain Analysis',
  '/vendor': 'Vendor Risk Intelligence',
  '/audit': 'Audit Trail Engine',
  '/ocr': 'OCR Invoice Upload',
  '/itc-calc': 'ITC & Reversal Calculator',
  '/predict': 'Predictive Risk Model',
  '/graph': 'Knowledge Graph Explorer',
  '/traversal': 'Live Graph Traversal Engine',
};

function Layout() {
  const location = useLocation();
  const title = PAGE_TITLES[location.pathname] || 'GraphLedger AI';

  return (
    <>
      <Sidebar />
      <main className="main">
        <Topbar title={title} />
        <div className="content">
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/recon" element={<Reconciliation />} />
            <Route path="/chain" element={<ITCChain />} />
            <Route path="/vendor" element={<VendorRisk />} />
            <Route path="/audit" element={<AuditTrail />} />
            <Route path="/ocr" element={<OCRUpload />} />
            <Route path="/itc-calc" element={<ITCCalculator />} />
            <Route path="/predict" element={<Prediction />} />
            <Route path="/graph" element={<GraphExplorer />} />
            <Route path="/traversal" element={<Traversal />} />
          </Routes>
        </div>
      </main>
      <Chatbot />
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Layout />
    </BrowserRouter>
  );
}
