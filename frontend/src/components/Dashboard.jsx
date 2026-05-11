import React, {useEffect, useState} from 'react'
import axios from 'axios'

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
      const res = await axios.get('http://localhost:8000/scans')
      setScans(res.data)
    }catch(e){ console.error(e) }
    setLoading(false)
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">fallen_budgie — Dashboard</h1>
      {loading && <div>Loading…</div>}
      <div className="grid gap-4 grid-cols-1 md:grid-cols-2">
        {scans.map(s => (
          <div key={s.id} className="border rounded p-4 shadow-sm bg-white">
            <div className="flex justify-between items-start">
              <div>
                <div className="text-lg font-semibold">{s.target}</div>
                <div className="text-sm text-gray-500">{s.scan_type} — {s.status}</div>
              </div>
              <div>
                <span className={"px-2 py-1 rounded text-sm font-medium "+(
                  (severityFor(s)==='High')? 'bg-red-100 text-red-800':
                  (severityFor(s)==='Medium')? 'bg-yellow-100 text-yellow-800':'bg-green-100 text-green-800'
                )}>{severityFor(s)}</span>
              </div>
            </div>
            <div className="mt-3 text-sm text-gray-700">
              <div>Created: {s.created_at || '—'}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
