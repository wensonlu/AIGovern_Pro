import React, { Suspense } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Spin } from 'antd'
import ChatPanel from './components/AGUI/ChatPanel'

// Lazy load all pages for code splitting
const Dashboard = React.lazy(() => import('./pages/Dashboard'))
const Documents = React.lazy(() => import('./pages/Documents'))
const DataQuery = React.lazy(() => import('./pages/DataQuery'))
const SmartOps = React.lazy(() => import('./pages/SmartOps'))
const Diagnosis = React.lazy(() => import('./pages/Diagnosis'))
const Products = React.lazy(() => import('./pages/Products'))
const AgentSkills = React.lazy(() => import('./pages/AgentSkills'))
const AIAssistantDemo = React.lazy(() => import('./pages/AIAssistantDemo'))

// Fallback loading component
const PageLoader: React.FC = () => (
  <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
    <Spin tip="加载中..." />
  </div>
)

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/documents" element={<Documents />} />
          <Route path="/query" element={<DataQuery />} />
          <Route path="/operations" element={<SmartOps />} />
          <Route path="/diagnosis" element={<Diagnosis />} />
          <Route path="/products" element={<Products />} />
          <Route path="/skills" element={<AgentSkills />} />
          <Route path="/ai-demo" element={<AIAssistantDemo />} />
        </Routes>
      </Suspense>
      <ChatPanel />
    </BrowserRouter>
  )
}

export default App
