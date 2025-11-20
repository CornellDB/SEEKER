import { useState, useEffect, useContext } from 'react'
import { useNavigate } from 'react-router-dom'

import TableCard from '../../components/TableCard'
import FormDataCtxt from '../../utils/formData'
import {Apptest} from "../../pages/Appjs/Apptest";
import {Architecture} from "../../pages/Architecture/Architecture";
import MainTable from '../../components/MainTable'
import Xarrow from "react-xarrows";

import React from "react";
import { PieChart, Pie, Cell, Tooltip, Legend } from "recharts";

const PChart = () => {
    var colors = ["#8884d8", "#82ca9d", "#FFBB28", "#FF8042", "#AF19FF"];
    var pieData = [
       {
          name: "1",
          value: 14
       },
       {
          name: "2",
          value: 17
       },
       {
          name: "2",
          value: 16
       },
       {
          name: "4",
          value: 16
       },
       {
          name: "5",
          value: 10
       },
       ,
       {
          name: "6",
          value: 10
       },
       ,
       {
          name: "others",
          value: 17
       }
    ];
    var CustomTooltip = ({ active, payload, label }) => {
       if (active) {
          return (
          <div
             className="custom-tooltip"
             style={{
                backgroundColor: "white",
                padding: "5px",
                border: "1px solid #cccc"
             }}
          >
             <label>{`${payload[0].name} : ${payload[0].value}%`}</label>
          </div>
       );
    }
    return null;
    };
    return (
        <PieChart width={300} height={300}>
        <Pie
           data={pieData}
           color="#000000"
           dataKey="value"
           nameKey="name"
           cx="50%"
           cy="50%"
           outerRadius={120}
           fill="#white"
        >
           {pieData.map((entry, index) => (
              <Cell
                 key={`cell-${index}`}
                 fill={colors[index % colors.length]}
              />
           ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
        <Legend />
        </PieChart>
    );
 }
const Inspect = () => {
    let navigate = useNavigate();
    const [formData, setFormData] = useContext(FormDataCtxt)
    const [results, setResults] = useState([])
    const [activeTab, setActiveTab] = useState("tab1");


    const validData = (data) => {
        return data.attribute && data.task && data.file
    }
    const Test = (color1,color2,color3,color4,color5)=>{
        return Apptest(color1,color2,color3,color4,color5);
    }
    //currid is a random number given so that each button has a unique id even if we use same datasets multiple times
    
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
            <div className="">
                <div style={{ float:"right",width:"100%", backgroundColor:"#C4DDFF", height:"70px"}}>
                    <center><h4>GODDS</h4></center>
                </div>
                <div style={{ float:"left",width:"100%"}}>
                    <div style={{ float:"left", height:"780px",width: "20%", backgroundColor:"#C4DDFF", margin: "0px 25px 0px 0px"}}>
                    {
                    Test('lightgreen','lightgreen','lightgreen','lightgreen','lightyellow')}
                    </div>
                    <div style={{ float:"left", height:"780px",width: "20%",  margin: "0px 25px 0px 0px"}}>
                            <button style={{color:"black",position: "absolute", border:"0px", left: "25%", margin:"13px 0px 0px 0px"}}type="submit" id="without_augmentation" ><u>Execution Summary</u></button>
                            <br></br>
                            <br></br>
                            <p>Number of identified candidates: 9200 <br></br>
                            Number of useful augmentations: 5 <br></br>
                            Number of Queries: 270 <br></br>
                            Cluster size distribution:
                            </p>
                            <div style={{ float:"left", height:"300px",width: "100%", backgroundColor:"#C4DDFF", margin: "0px 25px 0px 0px"}}>{PChart()}</div>
                    </div>
                    <div style={{ height:"780px", float:"right",width:"0%"}}>
                        
                        <button style={{color:"black",position: "absolute", border:"0px", right: "25%", margin:"13px 0px 0px 0px"}}type="submit" id="without_augmentation" ><u>GODDS Components</u></button>
                        <br></br>
                        <br></br>
                        {
                        Architecture("base.csv")
                        }
                    </div>
                </div>
            </div>
        )
    } else {
        navigate("/")
    }
    
}

export default Inspect;


//<div style={{
//                    display: "flex",
//                    flexDirection: "row",
//                    flexWrap: "wrap"
//                }}>
//
//                    { results.map(r => <TableCard name={r.name} score={r.score} preview={r.preview} />) }
//                    {Test('lightgreen','lightgreen','lightgreen','lightyellow')}
//                </div>



