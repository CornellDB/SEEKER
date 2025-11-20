import { useState, useEffect, useContext } from 'react'
import { useNavigate } from 'react-router-dom'

import TableCard from '../../components/TableCard'
import FormDataCtxt from '../../utils/formData'
import {Apptest} from "../../pages/Appjs/Apptest";
import MainTable from '../../components/MainTable'
import Xarrow from "react-xarrows";


const Provenance = () => {
    let navigate = useNavigate();
    const [formData, setFormData] = useContext(FormDataCtxt)
    const [results, setResults] = useState([])
    const [activeTab, setActiveTab] = useState("tab1");


    const validData = (data) => {
        return data.attribute && data.task && data.file
    }
    const Test = (color1,color2,color3,color4)=>{
        return Apptest(color1,color2,color3,color4);
    }
    useEffect(() => {
        if (formData) {
            const url = '/api/results'
            
            var data = new FormData();
            for (const itemName in formData) {
                console.log(itemName)
                data.append(itemName, formData[itemName])
            }
            fetch(url, {
                method: 'post',
                body: data
            })
            .then(res => res.json())
            .then(data => setResults(data))
        }
    }, [formData])
    const clst=[]
    const clst2=["School Type","ES","ES/MS","MS","MS/HS","HS","ECC","HST"]
    if (validData(formData)) {
        return (
            <div className='container'>
                <h2>Metam Results</h2>
                <b>Utility without external data:</b> 0.64
                <br></br>
                Identified 5 datasets to boost task performance
                <br></br>
                <hr></hr>
                <div style={{width: "100%"}}>
                <div  style={{float:"left", width: "50%", backgroundColor:"white", margin: "0px 25px 0px 0px"}}>
                <b>New column: School Type </b><br></br>
                Base Table&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; New table identified
                <br></br>
                <MainTable 
                        id="elem1"
                        name={formData.file.name}
                        preview={formData.dataset.data}
                        wid="10%"
                        clst={clst}
                    />
                    &nbsp;&nbsp;&nbsp;  &nbsp;&nbsp;&nbsp;
                <MainTable 
                        id="elem2"
                        name={formData.file.name}
                        preview={formData.dataset.data}
                        wid="10%"
                        clst={clst}
                    />
                </div>
                
                <div style={{float:"right", width: "40%", backgroundColor:"white", margin: "0px 25px 0px 0px"}}>
                <button style={{position: "absolute", left: "25%", margin:"275px 0px 0px 0px"}}type="submit" id="join" >Join</button>
                <button style={{position: "absolute", left: "15%", margin:"605px 0px 0px 0px"}}type="submit" id="task" >{formData.task}</button>
                <button style={{position: "absolute", left: "40%", margin:"605px 0px 0px 0px"}}type="submit" id="score" >0.68</button>
                <Xarrow
                start="elem1" //can be react ref
                end="join"
                path="straight" //or an id
            />
            
            <Xarrow
                start="elem2" //can be react ref
                end="join"
                path="straight" //or an id
            />
            <Xarrow
                start="joineddata" //can be react ref
                end="task"
                path="straight" //or an id
            />
            <Xarrow
                start="task" //can be react ref
                end="score"
                path="straight" //or an id
            />
                </div>
                <div style={{float:"right", width: "30%", backgroundColor:"white", margin: "500px 35px 0px 0px"}}>
                    <a href="">Show all useful Candidates</a><br></br>
                    </div>
                </div>
                
                <br></br>
                <br></br>
                <br></br>
                <br></br>
                <br></br>
                <br></br>
                <br></br>
                <br></br>
                <br></br>
                <br></br>
                
                <br></br>
                <br></br>
                <br></br>
                <br></br>
                Added new column: School Type
                <br></br>
                <MainTable 
                        id="joineddata"
                        name="Added new column School Type"
                        preview={formData.dataset.data}
                        wid="50%"
                        clst={clst2}
                    />
                    <a href="">Download</a>
                    
                    <Xarrow
                        start="join" //can be react ref
                        end="joineddata"
                        path="straight" //or an id
                    />
                <br></br>
                <br></br>
                <br></br>
                <br></br>
                <br></br>
                
                {Test('lightgreen','lightgreen','lightgreen','lightyellow')}
                
            </div>
        )
    } else {
        navigate("/")
    }
    
}

export default Provenance;


//<div style={{
//                    display: "flex",
//                    flexDirection: "row",
//                    flexWrap: "wrap"
//                }}>
//
//                    { results.map(r => <TableCard name={r.name} score={r.score} preview={r.preview} />) }
//                    {Test('lightgreen','lightgreen','lightgreen','lightyellow')}
//                </div>



