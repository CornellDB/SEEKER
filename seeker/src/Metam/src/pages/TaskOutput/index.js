// src/pages/TaskOutput/index.jsx
import React, { useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import MainTable from "../../components/MainTable";
import FormDataCtxt from "../../utils/formData";
import { Apptest } from "../../pages/Appjs/Apptest";
import Xarrow from "react-xarrows";

const styles = {
  container:   { position: "relative", height: "100%", width: "100%" },
  header:      { float: "right", width: "100%", backgroundColor: "#C4DDFF", height: 70 },
  sidebar:     { float: "left", height: "calc(100vh - 70px)", width: "20%", backgroundColor: "#C4DDFF" },
  content:     { marginLeft: "20%", padding: 20, position: "relative", minHeight: 400 },
  tableBox:    { position: "absolute", top: 80, left: 20, width: "40%" },
  taskBubble:  id => ({ position: "absolute", top: 80 + 60 * id, left: "55%", padding: "8px 16px", backgroundColor: "#F9F5EB", borderRadius: 4 }),
  scoreBubble: id => ({ position: "absolute", top: 80 + 60 * id, left: "75%", padding: "8px 16px", backgroundColor: "#F9F5EB", borderRadius: 4 }),
  external:    { position: "absolute", top: 380, left: 20, width: "80%" }
};

export default function TaskOutput() {
  const navigate = useNavigate();
  const [formData] = useContext(FormDataCtxt);
  const { jobId, fileName, preview, variants = [] } = formData;
  const [joinpathPath, setJoinpathPath] = useState(null);
  const [folderPaths, setFolderPaths] = useState([]);

  // per-variant score and loading state
  const [scores, setScores]     = useState({});
  const [loading, setLoading]   = useState({});

  // calculate each variant's utility
  useEffect(() => {
    variants.forEach((v, idx) => {
      if (!jobId || !v.task || !v.attribute || !v.metric) return;
      if (scores[v.id] != null) return; // already fetched

      setLoading(l => ({ ...l, [v.id]: true }));
      fetch("/api/utility", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: jobId, task: v.task, attribute: v.attribute, utilityMetric: v.metric })
      })
        .then(res => res.ok ? res.json() : Promise.reject("Calc failed"))
        .then(json => setScores(s => ({ ...s, [v.id]: json.score })))
        .catch(err => {
          console.error(`Variant ${v.id} error`, err);
          setScores(s => ({ ...s, [v.id]: null }));
        })
        .finally(() => setLoading(l => ({ ...l, [v.id]: false })));
    });
  }, [variants, jobId]);
  // 上传单个 joinable paths 文件
  const onJoinPathChange = e => {
    const file = e.target.files[0];
    if (!file) return;
    const data = new FormData();
    data.append("job_id", jobId);
    data.append("joinpath_file", file);
    fetch("/api/upload/joinpath", {
      method: "POST",
      body: data
    })
      .then(res => res.ok ? res.json() : Promise.reject(res.statusText))
      .then(json => {
        // 后端会返回 {"job_id": ..., "path": savedPath}
        setJoinpathPath(json.path);
        console.log("JoinPath saved to:", json.path);
      })
      .catch(console.error);
  };

  // 上传整个文件夹（多选文件）
  const onFolderChange = e => {
    const files = Array.from(e.target.files);
    if (!files.length) return;
    const data = new FormData();
    data.append("job_id", jobId);
    files.forEach(f => data.append("folder_files", f));
    fetch("/api/upload/folder", {
      method: "POST",
      body: data
    })
      .then(res => res.ok ? res.json() : Promise.reject(res.statusText))
      .then(json => {
        // 后端会返回 {"job_id": ..., "paths": [savedPaths]}
        setFolderPaths(json.paths);
        console.log("Folder files saved to:", json.paths);
      })
      .catch(console.error);
  };
  // navigate to results (METAM) page
  const goResults = () => navigate("/results");

  return (
    <div style={styles.container}>
      {/* HEADER */}
      <div style={styles.header}><center><h4>GODDS</h4></center></div>
      {/* SIDEBAR */}
      <div style={styles.sidebar}>{Apptest("lightgreen","lightgreen","lightyellow","lightgrey","lightgrey")}</div>

      {/* MAIN CONTENT: one preview + arrows b/w variants */}
      <div style={styles.content}>
        {/* Preview table (shared) */}
        <div style={styles.tableBox} id="csv">
          {preview && <MainTable name={fileName} preview={preview} wid="100%" clst={[]} />}
        </div>

        {/* For each variant, render task and score bubbles + arrows */}
        {variants.map((v, idx) => (
          <React.Fragment key={v.id}>
            <button id={`task${v.id}`} style={styles.taskBubble(idx)}>
              {v.task}
            </button>
            <button id={`score${v.id}`} style={styles.scoreBubble(idx)}>
              {loading[v.id]
                ? "Calculating..."
                : scores[v.id] != null
                  ? `Score: ${scores[v.id].toFixed(4)}`
                  : "Score: N/A"
              }
            </button>
            {/* arrow from table to task */}
            <Xarrow start="csv" end={`task${v.id}`} strokeWidth={2} color="#000" />
            {/* arrow from task to score */}
            <Xarrow start={`task${v.id}`} end={`score${v.id}`} strokeWidth={2} color="#000" />
          </React.Fragment>
        ))}

{/* shared external inputs */}
        <div style={styles.external}>
          <div>
            <label>Choose external folder:</label><br />
            <input
              type="file"
              webkitdirectory=""   // 让浏览器一次选整个文件夹
              directory=""
              multiple
              onChange={onFolderChange}
            />
          </div>
          <div style={{ marginTop: 12 }}>
            <label>Upload joinable paths file:</label><br />
            <input
              type="file"
              accept=".json,.csv"
              onChange={onJoinPathChange}
            />
          </div>
          <div style={{ marginTop: 16 }}>
            <button
              onClick={goResults}
              style={{ ...styles.taskBubble(0), position: 'static', marginRight: 8 }}
            >
              Identify useful augmentations
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}