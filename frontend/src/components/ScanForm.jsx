import React, {useState} from 'react'
import api from '../lib/api'
import { useNavigate } from 'react-router-dom'

export default function ScanForm(){
  const [target, setTarget] = useState('')
  const [type, setType] = useState('network')
  const [scanMode, setScanMode] = useState('Full Scan')
  const [selectedTools, setSelectedTools] = useState(['nmap','nuclei'])
  const [isScheduled, setIsScheduled] = useState(false)
  const [cronSchedule, setCronSchedule] = useState('')
  const [loading, setLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState(null)
  const [created, setCreated] = useState(null)
  const navigate = useNavigate()

  async function submit(e){
    e.preventDefault()
    setLoading(true)
    setErrorMsg(null)
    try{
      const payload = {
        target,
        scan_type: type,
        scan_mode: scanMode,
        selected_tools: scanMode === 'Full Scan' ? ['nmap','nuclei'] : selectedTools,
        is_scheduled: !!isScheduled,
        cron_schedule: isScheduled ? cronSchedule : null,
      }

      const res = await api.post('/scan', payload)
      setCreated(res.data)
      // navigate to detail page
      navigate(`/scans/${res.data.id}`)
    }catch(err){
      console.error(err)
      const msg = err?.response?.data?.detail || err.message || 'Failed to create scan'
      setErrorMsg(msg)
    }
    setLoading(false)
  }

  function toggleTool(tool){
    const copy = new Set(selectedTools)
    if(copy.has(tool)) copy.delete(tool)
    else copy.add(tool)
    // if nuclei gets unchecked remove dependent tools
    if(!copy.has('nuclei')) copy.delete('katana')
    setSelectedTools(Array.from(copy))
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

        <div className="mb-3">
          <div className="flex gap-2">
            <button type="button" onClick={()=>setScanMode('Full Scan')} className={`px-3 py-1 rounded ${scanMode==='Full Scan' ? 'bg-indigo-600 text-white' : 'bg-white border'}`}>Full Scan</button>
            <button type="button" onClick={()=>setScanMode('Custom Scan')} className={`px-3 py-1 rounded ${scanMode==='Custom Scan' ? 'bg-indigo-600 text-white' : 'bg-white border'}`}>Custom Scan</button>
          </div>
          {scanMode === 'Custom Scan' && (
            <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
              {['nmap','nuclei','subfinder','katana'].map(tool => {
                const disabled = (tool === 'katana' && !selectedTools.includes('nuclei'))
                return (
                  <label key={tool} className={`flex items-center gap-2 ${disabled? 'opacity-50': ''}`}>
                    <input type="checkbox" checked={selectedTools.includes(tool)} disabled={disabled} onChange={e=>toggleTool(tool)} />
                    <span className="capitalize">{tool}</span>
                  </label>
                )
              })}
            </div>
          )}
        </div>

        <div className="mb-4">
          <label className="flex items-center gap-3">
            <input type="checkbox" checked={isScheduled} onChange={e=>setIsScheduled(e.target.checked)} />
            <span className="text-sm">Wiederkehrender Scan (Cron)</span>
          </label>
          {isScheduled && (
            <input className="w-full border rounded px-3 py-2 mt-2" placeholder="Cron expression, e.g. 0 3 * * 1" value={cronSchedule} onChange={e=>setCronSchedule(e.target.value)} />
          )}
        </div>

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
