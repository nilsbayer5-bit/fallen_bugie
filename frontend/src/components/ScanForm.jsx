import React, {useState} from 'react'
import axios from 'axios'
import api from '../lib/api'
import { useNavigate } from 'react-router-dom'

export default function ScanForm(){
  const [target, setTarget] = useState('')
  const [type, setType] = useState('network')
  const [loading, setLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState(null)
  const [created, setCreated] = useState(null)
  const navigate = useNavigate()

  async function submit(e){
    e.preventDefault()
    setLoading(true)
    setErrorMsg(null)
    try{
      const res = await api.post('/scan', { target, scan_type: type })
      setCreated(res.data)
      // navigate to detail page
      navigate(`/scans/${res.data.id}`)
    }catch(err){
      console.error(err)
      const msg = err?.response?.data?.detail || err.message || 'Failed to create scan'
      setErrorMsg(msg)
      alert(`Failed to create scan: ${msg}`)
    }
    setLoading(false)
  }

  return (
    <div className="max-w-xl">
      <h2 className="text-xl font-semibold mb-4">New Scan</h2>
      <form onSubmit={submit} className="bg-white p-4 rounded border">
        <label className="block mb-2 text-sm font-medium">Target (IP or URL)</label>
        <input className="w-full border rounded px-3 py-2 mb-3" value={target} onChange={e=>setTarget(e.target.value)} placeholder="e.g. 192.168.1.1 or https://example.com" />

        <label className="block mb-2 text-sm font-medium">Scan Type</label>
        <select value={type} onChange={e=>setType(e.target.value)} className="w-full border rounded px-3 py-2 mb-4">
          <option value="network">Network (nmap)</option>
          <option value="web">Web (nuclei)</option>
        </select>

        <div className="flex items-center gap-3">
          <button type="submit" className="bg-indigo-600 text-white px-4 py-2 rounded" disabled={loading}>{loading? 'Starting…' : 'Start Scan'}</button>
        </div>
      </form>
      {errorMsg && <div className="mt-3 text-sm text-red-600">{errorMsg}</div>}
      {created && (
        <div className="mt-3 text-sm text-gray-700 border rounded p-3 bg-gray-50">
          <div className="font-medium">Created scan id: {created.id}</div>
          <pre className="text-xs mt-2">{JSON.stringify(created, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}
