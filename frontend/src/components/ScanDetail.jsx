import React, {useEffect, useState} from 'react'
import axios from 'axios'
import { useParams } from 'react-router-dom'

function PortList({hosts}){
  if(!hosts || hosts.length===0) return <div className="text-sm text-gray-500">No results yet</div>
  return (
    <div className="mt-3 space-y-3">
      {hosts.map(h=> (
        <div key={h.host} className="border rounded p-3 bg-gray-50">
          <div className="font-medium">{h.host} — {h.status}</div>
          <div className="mt-2 text-sm">
            {h.ports && h.ports.length>0 ? (
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-gray-500"><th>Port</th><th>State</th><th>Service</th><th>Product</th></tr>
                </thead>
                <tbody>
                  {h.ports.map(p => (
                    <tr key={p.port}><td className="pr-4">{p.port}</td><td>{p.state}</td><td>{p.name}</td><td>{p.product||''} {p.version||''}</td></tr>
                  ))}
                </tbody>
              </table>
            ) : <div className="text-sm text-gray-500">No open ports found</div>}
          </div>
        </div>
      ))}
    </div>
  )
}

export default function ScanDetail(){
  const { id } = useParams()
  const [scan, setScan] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(()=>{ fetchScan() }, [id])

  async function fetchScan(){
    setLoading(true)
    try{
      const res = await axios.get(`http://localhost:8000/scans/${id}`)
      setScan(res.data)
    }catch(e){ console.error(e) }
    setLoading(false)
  }

  if(loading) return <div>Loading…</div>
  if(!scan) return <div className="text-gray-600">Scan not found</div>

  return (
    <div>
      <h2 className="text-xl font-semibold">Scan: {scan.target}</h2>
      <div className="mt-3 text-sm text-gray-600">Type: {scan.scan_type} — Status: {scan.status}</div>

      {scan.result ? (
        <PortList hosts={scan.result.hosts} />
      ) : (
        <div className="mt-4 text-sm text-gray-500">No results yet. Refresh to see updates.</div>
      )}
    </div>
  )
}
