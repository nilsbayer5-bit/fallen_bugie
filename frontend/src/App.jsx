import React from 'react'
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import Dashboard from './components/Dashboard'
import ScanForm from './components/ScanForm'
import ScanDetail from './components/ScanDetail'

export default function App(){
  return (
    <BrowserRouter>
      <div className="min-h-screen">
        <nav className="bg-white border-b">
          <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
            <Link to="/" className="text-xl font-bold">fallen_budgie</Link>
            <div className="space-x-3">
              <Link to="/" className="text-sm text-gray-600 hover:text-gray-900">Dashboard</Link>
              <Link to="/scan" className="text-sm text-gray-600 hover:text-gray-900">New Scan</Link>
            </div>
          </div>
        </nav>

        <main className="max-w-6xl mx-auto p-6">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/scan" element={<ScanForm />} />
            <Route path="/scans/:id" element={<ScanDetail />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
