import TablePreview from "../TablePreview";
import "./index.css";
import { useContext, useEffect, useState } from "react"

function sayHello() {
    console.log("Hello there !!");
  }

const Checkbox = props => (
    <input type="checkbox" {...props} />
  )

const CkBox = () => {
    const state = { checked: false }
    const handleCheckboxChange = event =>
    state.checked=true
    {
    
  }
}
const MainTable = ({ id, name, source, relationship, score, preview, wid, clst }) => {
    const [checked, setChecked] = useState(false);
    console.log(name,id,source)
    const handleChange = () => {
        console.log(name,!checked)
        var div_obj = document.querySelector('#'+CSS.escape(id));
        if (!checked){
            div_obj.style.setProperty('border', '5px solid red');
        }else{
            div_obj.style.setProperty('border', '1px solid gray');  
        }
        setChecked(!checked);
    };
    return <div id={id} style={{width:wid}} className="card_wrapper" onClick={handleChange}>
        <TablePreview preview={preview} colorlst={clst} />
    </div>

}


export default MainTable;