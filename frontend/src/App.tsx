import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Documents from './pages/Documents'
import DataQuery from './pages/DataQuery'
import SmartOps from './pages/SmartOps'
import Diagnosis from './pages/Diagnosis'
import ChatPanel from './components/AGUI/ChatPanel'

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/documents" element={<Documents />} />
        <Route path="/query" element={<DataQuery />} />
        <Route path="/operations" element={<SmartOps />} />
        <Route path="/diagnosis" element={<Diagnosis />} />
      </Routes>
      <ChatPanel />
    </BrowserRouter>
  )
}

export default App
