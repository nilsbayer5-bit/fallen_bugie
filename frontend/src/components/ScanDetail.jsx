import React, {useEffect, useState} from 'react'
import axios from 'axios'
import api from '../lib/api'
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

function NucleiList({nuclei}){
  if(!nuclei) return <div className="text-sm text-gray-500">No nuclei results</div>
  if(Array.isArray(nuclei)){
    if(nuclei.length===0) return <div className="text-sm text-gray-500">No nuclei findings</div>
    return (
      <div className="mt-3 space-y-2">
        {nuclei.map((f, idx) => (
          <div key={idx} className="border rounded p-3 bg-white">
            <div className="text-sm font-medium">{(f.info && f.info.name) || f.name || f.template || 'Finding'}</div>
            <div className="text-xs text-gray-600 mt-1">Severity: {(f.info && f.info.severity) || f.severity || 'info'}</div>
            <pre className="text-xs mt-2 bg-gray-50 p-2 rounded overflow-auto">{JSON.stringify(f, null, 2)}</pre>
          </div>
        ))}
      </div>
    )
  }
  // nuclei returned an object (likely an error)
  return <div className="text-sm text-red-600">{nuclei.error || JSON.stringify(nuclei)}</div>
}

export default function ScanDetail(){
  const { id } = useParams()
  const [scan, setScan] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(()=>{ fetchScan() }, [id])

  async function fetchScan(){
    setLoading(true)
    try{
      const res = await api.get(`/scans/${id}`)
      setScan(res.data)
    }catch(e){ console.error(e) }
    setLoading(false)
  }

  if(loading) return <div>Loading…</div>
  if(!scan) {
    return <div className="text-gray-600">Scan not found — check backend or that the id is correct.</div>
  }

  return (
    <div>
      <h2 className="text-xl font-semibold">Scan: {scan.target}</h2>
      <div className="mt-3 text-sm text-gray-600">Type: {scan.scan_type} — Status: {scan.status}</div>
      <div className="mt-2 flex items-center gap-3">
        <div>
          <span className={`px-2 py-1 rounded text-sm font-medium ${
            (scan.overall_risk==='Critical')? 'bg-red-800 text-white':
            (scan.overall_risk==='High')? 'bg-orange-500 text-white':
            (scan.overall_risk==='Medium')? 'bg-yellow-400 text-black':
            (scan.overall_risk==='Low')? 'bg-blue-500 text-white':'bg-green-600 text-white'
          }`}>{scan.overall_risk || '—'}</span>
        </div>
        <div className="text-sm text-gray-600">{scan.risk_explanation || 'No explanation available'}</div>
      </div>

      {/* Nmap/network results */}
      <div className="mt-4">
        <h3 className="font-medium">Network results</h3>
        {scan.result && (scan.result.hosts || (scan.result.nmap && scan.result.nmap.hosts)) ? (
          <PortList hosts={scan.result.hosts || (scan.result.nmap && scan.result.nmap.hosts)} />
        ) : (
          <div className="mt-2 text-sm text-gray-500">No network results yet.</div>
        )}
      </div>

      {/* Nuclei/web results */}
      <div className="mt-6">
        <h3 className="font-medium">Web (nuclei) results</h3>
        <div className="mt-2">
          {scan.result && (scan.result.nuclei !== undefined) ? (
            <NucleiList nuclei={scan.result.nuclei} />
          ) : (
            <div className="text-sm text-gray-500">No nuclei results yet.</div>
          )}
        </div>
      </div>
    </div>
  )
}
