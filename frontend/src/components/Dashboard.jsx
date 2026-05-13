import React, {useEffect, useState} from 'react'
import axios from 'axios'
import api from '../lib/api'

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
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Severity</th>
                <th className="px-4 py-3">Created</th>
                <th className="px-4 py-3">Details</th>
              </tr>
            </thead>
            <tbody>
              {scans.map(s => (
                <tr key={s.id} className="border-t text-sm">
                  <td className="px-4 py-3">{s.target}</td>
                  <td className="px-4 py-3">{s.scan_type}</td>
                  <td className="px-4 py-3">{s.status}</td>
                  <td className="px-4 py-3">
                    <span className={"px-2 py-1 rounded text-sm font-medium " + (
                      (severityFor(s)==='High')? 'bg-red-100 text-red-800':
                      (severityFor(s)==='Medium')? 'bg-yellow-100 text-yellow-800':'bg-green-100 text-green-800'
                    )}>{severityFor(s)}</span>
                  </td>
                  <td className="px-4 py-3">{s.created_at || '—'}</td>
                  <td className="px-4 py-3"><Link to={`/scans/${s.id}`} className="text-indigo-600">View</Link></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    )
}
