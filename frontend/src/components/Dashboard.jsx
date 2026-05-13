import React, {useEffect, useState} from 'react'
import { Link } from 'react-router-dom'
import api from '../lib/api'
import { Trash2, DownloadCloud } from 'lucide-react'

function severityFor(scan) {
  // Simple heuristic for demo: if port 22 open => High, 80/443 => Medium else Low
  try {
    const hosts = scan.result?.hosts || []
    for (const h of hosts) {
      for (const p of h.ports || []) {
        if (p.port === 22 && p.state === 'open') return 'High'
        if ((p.port === 80 || p.port === 443) && p.state === 'open') return 'Medium'
      }
    }
  } catch(e){ }
  return 'Low'
}

export default function Dashboard(){
  const [scans, setScans] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(()=>{ fetchScans() }, [])

  async function fetchScans(){
    setLoading(true)
    try{
      const res = await api.get('/scans')
      setScans(res.data)
    }catch(e){ console.error(e) }
    setLoading(false)
  }

  async function deleteScan(id){
    if(!confirm('Delete scan '+id+'?')) return
    try{
      await api.delete(`/scans/${id}`)
      fetchScans()
    }catch(e){ console.error(e); alert('Failed to delete') }
  }

  async function downloadReport(id){
    try{
      const res = await api.get(`/scans/${id}/report`, { responseType: 'blob' })
      const blob = new Blob([res.data], { type: 'application/json' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `scan_${id}_report.json`
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
    }catch(e){ console.error(e); alert('Failed to download report') }
  }

    return (
      <div>
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <Link to="/scan" className="inline-block bg-indigo-600 text-white px-4 py-2 rounded shadow-sm">New Scan</Link>
        </div>

        {loading && <div>Loading…</div>}

        <div className="bg-white border rounded shadow-sm">
          <table className="w-full table-auto">
            <thead className="bg-gray-50 text-left text-sm text-gray-600">
              <tr>
                <th className="px-4 py-3">Target</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Mode</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Risk</th>
                <th className="px-4 py-3">Created</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {scans.map(s => (
                <tr key={s.id} className="border-t text-sm">
                  <td className="px-4 py-3">{s.target}</td>
                  <td className="px-4 py-3">{s.scan_type}</td>
                  <td className="px-4 py-3">{s.scan_mode || '—'}</td>
                  <td className="px-4 py-3">{s.status}</td>
                  <td className="px-4 py-3">
                    {(() => {
                      const r = s.overall_risk || severityFor(s)
                      const map = {
                        'Critical': 'bg-red-800 text-white',
                        'High': 'bg-orange-500 text-white',
                        'Medium': 'bg-yellow-400 text-black',
                        'Low': 'bg-blue-500 text-white',
                        'Safe': 'bg-green-600 text-white',
                      }
                      const cls = map[r] || 'bg-gray-100 text-gray-800'
                      return <span className={`px-2 py-1 rounded text-sm font-medium ${cls}`}>{r}</span>
                    })()}
                  </td>
                  <td className="px-4 py-3">{s.created_at || '—'}</td>
                  <td className="px-4 py-3 flex gap-2">
                    <Link to={`/scans/${s.id}`} className="text-indigo-600">View</Link>
                    <button onClick={()=>downloadReport(s.id)} title="Download report" className="p-2 rounded hover:bg-gray-100"><DownloadCloud size={16} /></button>
                    <button onClick={()=>deleteScan(s.id)} title="Delete" className="p-2 rounded hover:bg-gray-100 text-red-600"><Trash2 size={16} /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    )
}
