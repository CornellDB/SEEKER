// src/pages/Input/index.js
import React, { useContext, useState, useCallback, useEffect } from "react";
import { useNavigate } from "react-router-dom";

import MainTable from "../../components/MainTable";
import FormDataCtxt from "../../utils/formData";
import { Apptest } from "../../pages/Appjs/Apptest";

const styles = {
  container:      { overflow: "hidden" },
  header:         { float: "right", width: "100%", backgroundColor: "#C4DDFF", height: 70 },
  sidebar:        { float: "left", height: 780, width: "20%", backgroundColor: "#C4DDFF", marginRight: 25 },
  main:           { float: "left", width: "60%", padding: 20 },
  config:         { float: "left", width: "30%", padding: 20 },
  previewBox:     { border: "1px solid #ccc", padding: 12, minHeight: 200 },
  button:         { padding: "8px 16px", border: "1px solid #888", cursor: "pointer" },
  disabledButton: { backgroundColor: "#ccc", cursor: "default" },
  taskButton:     { marginRight: 8, marginBottom: 8 },
  variantPanel:   { border: "1px solid #aaa", padding: 12, marginBottom: 12 },
  fieldGroup:     { marginTop: 8 },
  checkboxContainer: {
    display: "flex",
    alignItems: "center",
    marginBottom: 4,
    cursor: "pointer",
    userSelect: "none",
  },
  hiddenCheckbox: {
    position: "absolute",
    opacity: 0,
    width: 0,
    height: 0,
  },
  box: {
    width: 16,
    height: 16,
    border: "2px solid black",
    marginRight: 8,
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: 14,
    lineHeight: 1,
  },
  labelText: {},
};

const STEPS         = ["classification", "regression", "what-if", "how-to", "other"];
const CLASS_METRICS = ["accuracy", "recall", "f1"];
const REG_METRICS   = ["mse", "r2"];
const COLOR_PALETTE = ["#8884d8", "#82ca9d", "#ffc658", "#ff7300", "#0088FE"];

export default function Input() {
  const navigate = useNavigate();
  const [formData, setFormData] = useContext(FormDataCtxt);
  const { jobId, fileName, preview, variants = [] } = formData;

  // 1) load global options
  const [configOptions, setConfigOptions] = useState({ queryMethods: [], profilers: [] });
  useEffect(() => {
    fetch("/api/config/options")
      .then(r => r.ok ? r.json() : Promise.reject(r.statusText)) // if r is ok, parse json,
      .then(setConfigOptions) //then pass the parsed json as parameter to setConfigOptions to update the configOptions.
      .catch(console.error);
  }, []);

  const [isUploading, setIsUploading]   = useState(false);
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [isPreparing, setIsPreparing]   = useState(false);

  const setFormField = useCallback((k, v) => {
    setFormData(f => ({ ...f, [k]: v }));
  }, [setFormData]);

  // ensure variants[] always exists
  useEffect(() => {
    if (!formData.variants) setFormField("variants", []);
  }, [formData.variants, setFormField]);

  // 2) variant helpers
  const updateVariant = (id, upd) => {
    setFormData(fd => ({
      ...fd,
      variants: fd.variants.map(v => v.id === id ? { ...v, ...upd } : v)
    }));
  };
  const removeVariant = id => {
    setFormData(fd => ({
      ...fd,
      variants: fd.variants.filter(v => v.id !== id)
    }));
  };
  const addVariant = () => {
    setFormData(fd => {
      const nextId = fd.variants.length
        ? Math.max(...fd.variants.map(v => v.id)) + 1
        : 0;
      return {
        ...fd,
        variants: [
          ...fd.variants,
          {
            id: nextId,
            task: null,
            attribute: null,
            metric: null,
            queryMethod: "",
            profilers: [],
            color: COLOR_PALETTE[nextId % COLOR_PALETTE.length]
          }
        ]
      };
    });
  };

  // 3) upload & preview
  const onFileChange = e => {
    const file = e.target.files[0];
    if (!file) return;
    setIsUploading(true);
    setFormField("fileName", file.name);
    const data = new FormData();
    data.append("dataset_file", file);

    fetch("/api/upload/file", { method: "POST", body: data })
      .then(async res => {
        if (!res.ok) throw new Error(await res.text());
        return res.json();
      })
      .then(({ job_id }) => {
        setFormField("jobId", job_id);
        fetchPreview(job_id);
      })
      .catch(console.error)
      .finally(() => setIsUploading(false));
  };

  const fetchPreview = job_id => {
    setIsPreviewing(true);
    fetch(`/api/preview/${job_id}?n=50`)
      .then(r => r.ok ? r.json() : Promise.reject(r.statusText))
      .then(data => setFormField("preview", data.preview))
      .catch(console.error)
      .finally(() => setIsPreviewing(false));
  };

  // 4) prepare (optional)
  const onPrepare = () => {
    if (!jobId) return;
    setIsPreparing(true);
    fetch("/api/prepare", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_id: jobId })
    })
      .then(r => {
        if (!r.ok) throw new Error("prepare failed");
        return fetchPreview(jobId);
      })
      .catch(console.error)
      .finally(() => setIsPreparing(false));
  };

  // 5) run
  // const onRunTask = () => {
  //   fetch("/api/metam/start", {
  //     method: "POST",
  //     headers: { "Content-Type": "application/json" },
  //     body: JSON.stringify({
  //       job_id:   jobId,
  //       variants: variants.map(v => ({
  //         task:        v.task,
  //         attribute:   v.attribute,
  //         metric:      v.metric,
  //         queryMethod: v.queryMethod,
  //         profilers:   v.profilers
  //       }))
  //     })
  //   }).finally(() => navigate("/taskoutput"));
  // };

  return (
    <div style={styles.container}>
      {/* HEADER */}
      <div style={styles.header}>
        <center><h4>GODDS</h4></center>
      </div>

      {/* SIDEBAR */}
      <div style={styles.sidebar}>
        {jobId
          ? Apptest("lightgreen","lightyellow","lightgrey","lightgrey","lightgrey")
          : Apptest("lightyellow","lightgrey","lightgrey","lightgrey","lightgrey")
        }
      </div>

      {/* MAIN: Upload & Preview */}
      <div style={styles.main}>
        {!jobId ? (
          <div style={{ textAlign: "center", marginTop: 200 }}>
            <h4>Upload your CSV dataset:</h4>
            <input
              type="file"
              accept=".csv"
              onChange={onFileChange}
              disabled={isUploading}
            />
          </div>
        ) : (
          <>
            <div><strong>Uploaded:</strong> {fileName}</div>
            <div style={styles.previewBox}>
              {isUploading
                ? <p>Uploading…</p>
                : isPreviewing
                  ? <p>Loading preview…</p>
                  : preview?.length
                    ? <MainTable name={fileName} preview={preview} wid="100%" clst={[]} />
                    : <p>No preview</p>
              }
            </div>
            <button
              onClick={onPrepare}
              disabled={isPreparing || !preview}
              style={{
                ...styles.button,
                ...(isPreparing ? styles.disabledButton : { backgroundColor: "#e7e7e7" })
              }}
            >
              {isPreparing ? "Preparing…" : "Prepare Dataset"}
            </button>
          </>
        )}
      </div>

      {/* CONFIG: Always visible once jobId exists */}
      {jobId && (
        <div style={styles.config}>
          {variants.map(v => (
            <div key={v.id} style={styles.variantPanel}>

              {/* Remove */}
              <button onClick={() => removeVariant(v.id)}>Remove</button>

              {/* 1. Task */}
              <div style={styles.fieldGroup}>
                <label>Task:</label><br/>
                {STEPS.map(step => (
                  <button
                    key={step}
                    onClick={() => updateVariant(v.id, { task: step, attribute: null, metric: null })}
                    style={{
                      ...styles.taskButton,
                      backgroundColor: v.task === step ? "#C4DDFF" : "#F9F5EB"
                    }}
                  >{step.charAt(0).toUpperCase() + step.slice(1)}</button>
                ))}
              </div>

              {/* 2. Attribute */}
              {(v.task === "classification" || v.task === "regression") && preview?.length > 0 && (
                <div style={styles.fieldGroup}>
                  <label>Attribute:</label><br/>
                  <select
                    value={v.attribute||""}
                    onChange={e => updateVariant(v.id, { attribute: e.target.value, metric: null })}
                    style={{ width:"100%" }}
                  >
                    <option value="" disabled>-- select --</option>
                    {Object.keys(preview[0]).map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
              )}

              {/* 3. Metric */}
              {v.task && (
                <div style={styles.fieldGroup}>
                  <label>Metric:</label><br/>
                  {(v.task==="classification"? CLASS_METRICS : v.task==="regression"? REG_METRICS : [])
                    .map(m => (
                      <button
                        key={m}
                        onClick={() => updateVariant(v.id, { metric: m })}
                        style={{
                          ...styles.taskButton,
                          backgroundColor: v.metric===m? "#C4DDFF":"#F9F5EB"
                        }}
                      >{m==="mse"? "MSE": m.toUpperCase()}</button>
                  ))}
                </div>
              )}

              {/* 4. Query Method */}
              <div style={styles.fieldGroup}>
                <label>GRP Query Method:</label><br/>
                <select
                  value={v.queryMethod}
                  onChange={e => updateVariant(v.id, { queryMethod: e.target.value })}
                  style={{ width:"100%" }}
                >
                  <option value="" disabled>-- select --</option>
                  {configOptions.queryMethods.map(qm =>
                    <option key={qm.key} value={qm.key}>{qm.label}</option>
                  )}
                </select>
              </div>


              {/* 5. Quatlity Scoring Method */}
              <div style={styles.fieldGroup}>
                <label>SEQ Scoring Method:</label><br/>
                <select
                  value={v.qualityScorers}
                  onChange={e => updateVariant(v.id, { qualityScorers: e.target.value })}
                  style={{ width:"100%" }}
                >
                  <option value="" disabled>-- select --</option>
                  {configOptions.qualityScorers.map(qm =>
                    <option key={qm.key} value={qm.key}>{qm.label}</option>
                  )}
                </select>
              </div>



              {/* 5. Profilers */}
              <div style={styles.fieldGroup}>
                <label>SEQ Profilers:</label><br/>
                {configOptions.profilers.map(p =>
                  <label key={p.key} style={styles.checkboxContainer}>
                    <input
                      type="checkbox"
                      checked={v.profilers.includes(p.key)}
                      onChange={e => {
                        const next = e.target.checked
                          ? [...v.profilers, p.key]
                          : v.profilers.filter(x => x !== p.key);
                        updateVariant(v.id, { profilers: next });
                      }}
                      style={styles.hiddenCheckbox}
                    />
                    <span style={styles.box}>
                      {v.profilers.includes(p.key) ? "✓" : ""}
                    </span>
                    <span style={styles.labelText}>{p.label}</span>
                  </label>
                )}
              </div>


            </div>
          ))}

          <button onClick={addVariant} style={styles.button}>Add Variant</button>
          <button onClick={() => navigate("/taskoutput")} style={{ ...styles.button, marginLeft:8 }}>Run Task</button>
        </div>
      )}

      <div style={{ clear:"both" }}/>
    </div>
  );
}
