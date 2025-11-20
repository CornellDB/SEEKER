// src/pages/Results/index.js
import React, { useContext, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import FormDataCtxt from '../../utils/formData';
import { Apptest } from '../../pages/Appjs/Apptest';
import {
  LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend,
  ResponsiveContainer
} from 'recharts';

const styles = {
  header:     { width: '100%', backgroundColor: '#C4DDFF', height: 70 },
  layout:     { display: 'flex', height: 'calc(100vh - 70px)' },
  sidebar:    { width: '20%', backgroundColor: '#C4DDFF', padding: 20 },
  content:    { flex: 1, display: 'flex', flexDirection: 'column', padding: 20, overflowY: 'auto' },
  chartWrap:  { flex: '0 0 300px' },
  logsWrap:   { flex: 1, marginTop: 20 },
  variantLogs:{ marginBottom: 24 }
};

export default function Results() {
  const navigate = useNavigate();
  const [formData] = useContext(FormDataCtxt);
  const { jobId, variants = [] } = formData;

  const [updatesByVar, setUpdatesByVar] = useState({}); //按 variant ID 存储每次迭代的得分数据
  const [augLogsByVar, setAugLogsByVar]   = useState({}); //存储每次“augmentation”事件的日志信息；
  const [isRunning,    setIsRunning]      = useState(true);
  const [error,        setError]          = useState(null);

  // start SSE and dispatch updates by variant
  useEffect(() => {
    if (!jobId) return navigate('/');

    fetch('/api/metam/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ job_id: jobId, variants })
    })
    .then(res => {
      if (!res.ok) throw new Error('Failed to start METAM');
      const es = new EventSource(`/api/metam/stream/${jobId}`);

      es.onmessage = e => {
        const msg = JSON.parse(e.data);
        const vid = msg.variant;

        if (msg.type === 'update') {
          setUpdatesByVar(prev => {
            const arr = prev[vid] || [];
            return { ...prev, [vid]: [...arr, { iteration: msg.iteration, score: msg.score }] };
          });
        } else if (msg.type === 'augmentation') {
          setAugLogsByVar(prev => {
            const arr = prev[vid] || [];
            return {
              ...prev,
              [vid]: [...arr, { name: msg.augmentation, score: msg.score, color: msg.Color }]
            };
          });
        } else if (msg.type === 'complete') {
          setIsRunning(false);
          es.close();
        }
      };

      es.onerror = () => {
        setError('Stream error');
        setIsRunning(false);
        es.close();
      };
    })
    .catch(err => {
      setError(err.message);
      setIsRunning(false);
    });
  }, [jobId, variants, navigate]);

  // build unified chart data
  const allIters = Array
    .from(new Set(Object.values(updatesByVar).flat().map(d => d.iteration)))
    .sort((a,b) => a - b);

  const chartData = allIters.map(iter => {
    const point = { iteration: iter };
    Object.entries(updatesByVar).forEach(([vid, arr]) => {
      const found = arr.find(d => d.iteration === iter);
      point[`v${vid}`] = found ? found.score : null;
    });
    return point;
  });

  return (
    <div>
      {/* Header */}
      <div style={styles.header}>
        <center><h4>GODDS</h4></center>
      </div>

      {/* Layout */}
      <div style={styles.layout}>

        {/* Sidebar */}
        <div style={styles.sidebar}>
          {Apptest('lightgreen','lightgreen','lightgreen','lightgreen','lightgrey')}
        </div>

        {/* Main Content */}
        <div style={styles.content}>

          {/* Overlaid Score Chart */}
          <div style={styles.chartWrap}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={chartData}
                margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="iteration" label={{ value: 'Iteration', position: 'insideBottom', offset: -5 }} />
                <YAxis label={{ value: 'Score', angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Legend />
                {variants.map(v => (
                  <Line
                    key={v.id}
                    dataKey={`v${v.id}`}
                    name={`Variant ${v.id}`}
                    stroke={v.color}
                    dot={false}
                    connectNulls
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Logs per Variant */}
          <div style={styles.logsWrap}>
            {isRunning
              ? <p>Running... {error && <span style={{ color: 'red' }}>{error}</span>}</p>
              : <p>Completed</p>
            }

            {variants.map(v => (
              <div key={v.id} style={styles.variantLogs}>
                <h5>Variant {v.id} Logs</h5>
                {(augLogsByVar[v.id] || []).map((item, idx) => (
                  <div key={idx}>
                    <b style={{ color: item.color }}>{item.name}</b> → <b>{item.score}</b>
                  </div>
                ))}
              </div>
            ))}
          </div>

        </div>
      </div>
    </div>
  );
}
