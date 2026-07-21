import { lazy, Suspense } from 'react';
import { HashRouter, Route, Routes } from 'react-router-dom';

import { AppShell } from './components/AppShell';
import { LoadingState } from './components/LoadingState';

const HomePage = lazy(() => import('./pages/HomePage').then((module) => ({ default: module.HomePage })));
const MethodologyPage = lazy(() => import('./pages/MethodologyPage').then((module) => ({ default: module.MethodologyPage })));
const NotFoundPage = lazy(() => import('./pages/NotFoundPage').then((module) => ({ default: module.NotFoundPage })));
const StockDetailPage = lazy(() => import('./pages/StockDetailPage').then((module) => ({ default: module.StockDetailPage })));

export default function App() {
  return (
    <HashRouter>
      <AppShell>
        <Suspense fallback={<div className="container page-space"><LoadingState /></div>}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/stock/:symbol" element={<StockDetailPage />} />
            <Route path="/methodology" element={<MethodologyPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </Suspense>
      </AppShell>
    </HashRouter>
  );
}
