import { BrowserRouter, Routes, Route } from "react-router-dom";
import FormDataCtxt from "./utils/formData";
import { useState } from "react";
import Input from "./pages/Input";
import {Apptest} from "./pages/Appjs/Apptest";
import Results from "./pages/Results";
import TaskOutput from "./pages/TaskOutput";
import Inspect from "./pages/Inspect";
import Provenance from "./pages/Provenance";

const App = () => {
    
    const [formData, setFormData] = useState({
        file: null,
        task: "",
        classification: 1,
        utilityMetric: 1,
        attribute: 1,
        dataset: null,
        matches: [],
        dataset:null
    })

    return (
        <BrowserRouter>

            <FormDataCtxt.Provider value={[ formData, setFormData ]}>
                <Routes>
                    <Route path="/" element={<Input />} />
                    <Route path="/taskoutput" element={<TaskOutput />} />
                    <Route path="/app" element={<Apptest />} />
                    <Route path="/results" element={<Results />} />
                    <Route path="/inspect" element={<Inspect />} />
                    <Route path="/provenance" element={<Provenance />} />
                </Routes>
            </FormDataCtxt.Provider>

        </BrowserRouter>
    )

}

export default App;