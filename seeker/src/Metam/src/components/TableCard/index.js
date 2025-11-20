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
     //this.setState({checked: event.target.checked })
    {
    return (
      <div>
        <label>
          <Checkbox
            checked={state.checked}
            onChange={handleCheckboxChange}
          />
          <span>Label Text</span>
        </label>
      </div>    
    ) 
  }
}
const TableCard = ({ id, name, source, relationship, score, preview }) => {
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
    const clst=[]
    return <div id={id} className="card_wrapper" onClick={handleChange}>
       <input align="left"
          type="checkbox"
          checked={checked}
          onChange={handleChange}
        />
        <Header
            key={name}
            name={name}
            source={source}
            relationship={relationship}
            score={score}
        />
        
        <TablePreview preview={preview} colorlst={clst} />
    </div>

}

const Header = ({ name, source, relationship, score}) => {
    
    return <div className="card_header">

        <div className="card_header_row">
            
            <span className="card_title">{ name }</span>
            
            <span className="card_header_subtitle">
                { name }
            </span>

        </div>

        <div className="card_header_row">
            <span className="card_header_text">

                { 
                    score && <strong>Score: { score }</strong>
                }

                {
                    relationship && relationship.map(r => r)
                }

            </span>
        </div>

    </div>
}

export default TableCard;