import React, {useState} from 'react'
import axios from 'axios'
import api from '../lib/api'
import { useNavigate } from 'react-router-dom'

export default function ScanForm(){
  const [target, setTarget] = useState('')
  const [type, setType] = useState('network')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  async function submit(e){
    e.preventDefault()
    setLoading(true)
    try{
      const res = await api.post('/scan', { target, scan_type: type })
      // navigate to detail page
      navigate(`/scans/${res.data.id}`)
    }catch(err){
      console.error(err)
      alert('Failed to create scan')
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
    </div>
  )
}
