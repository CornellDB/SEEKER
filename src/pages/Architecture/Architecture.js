import React from 'react';

import * as go from 'gojs';
import { ReactDiagram } from 'gojs-react';

import './Architecture.css';  // contains .diagram-component CSS
import Xarrow from "react-xarrows";

// ...

/**
 * Diagram initialization method, which is passed to the ReactDiagram component.
 * This method is responsible for making the diagram and initializing the model and any templates.
 * The model's data should not be set here, as the ReactDiagram component handles that via the other props.
 */
function initDiagram() {
  const $ = go.GraphObject.make;
  // set your license key here before creating the diagram: go.Diagram.licenseKey = "...";
  const diagram =
    $(go.Diagram,
      {
        'undoManager.isEnabled': true,  // must be set to allow for model change listening
        // 'undoManager.maxHistoryLength': 0,  // uncomment disable undo/redo functionality
        'clickCreatingTool.archetypeNodeData': { text: 'new node', color: 'lightblue' },
        model: new go.GraphLinksModel(
          {
            linkKeyProperty: 'key',  // IMPORTANT! must be defined for merges and data sync when using GraphLinksModel
          })
      });
  
  // define a simple Node template
  var before =
    $(go.Node, 'Auto',  // the Shape will go around the TextBlock
      new go.Binding('location', 'loc', go.Point.parse).makeTwoWay(go.Point.stringify),
      $(go.Shape, 'RoundedRectangle',
        { name: 'SHAPE', fill: 'white', strokeWidth: 0 },
        // Shape.fill is bound to Node.data.color
        new go.Binding('fill', 'color')),
        $(go.Picture, 'type',
        { row: 1, width: 50, height: 50, scale: 1.0 }),
      $(go.TextBlock,
        { margin: 8, editable: true },  // some room around the text
        new go.Binding('text').makeTwoWay()
      )
    );

    var after =
    $(go.Node, 'Auto',  // the Shape will go around the TextBlock
      new go.Binding('location', 'loc', go.Point.parse).makeTwoWay(go.Point.stringify),
      $(go.Shape, 'Ellipse',
        { name: 'SHAPE', fill: 'white', strokeWidth: 0 },
        // Shape.fill is bound to Node.data.color
        new go.Binding('fill', 'color')),
      $(go.Picture, new go.Binding("source", "type"),
        { row: 1, width: 50, height: 50, scale: 1.0 }),
      $(go.TextBlock,
        { margin: 8, editable: true },  // some room around the text
        new go.Binding('text').makeTwoWay()
      )
    );

    var templmap = new go.Map(); // In TypeScript you could write: new go.Map<string, go.Node>();
    // for each of the node categories, specify which template to use
    templmap.add("before", before);
    templmap.add("after", after);
    diagram.nodeTemplateMap = templmap;

  
  //diagram.add(
      //$(go.Part,
      //  $(go.Picture,  "https://hips.hearstapps.com/hmg-prod.s3.amazonaws.com/images/cute-cat-photos-1593441022.jpg?crop=0.669xw:1.00xh;0.166xw,0&resize=640:*")
      //));
     
      
  return diagram;
}

/**
 * This function handles any changes to the GoJS model.
 * It is here that you would make any updates to your React state, which is dicussed below.
 */
function handleModelChange(changes) {
  alert('GoJS model changed!');
}
const openInNewTab = url => {
  window.open(url,"_self");
};
// render function...
export function Architecture(fname) {
  return (
    <div style={{textAlign: "center", float:"right", width: "40%", backgroundColor:"#C4DDFF", margin: "0px 25px 0px 0px"}}>
      <br></br>
      
      <button style={{boxShadow: "2px 2px 2px 1px #808080", border: "1px solid black", backgroundColor:"#e7e7e7",color:"black", width:"250px",height:"40px",  color:"black",position: "absolute", right: "10%", margin:"5px 0px 0px 0px"}} type="submit" id="index"  onClick={() => openInNewTab('/')} ><h6><b>Index</b></h6> </button>
      <button style={{width:"250px",height:"40px",  backgroundColor:"white",color:"black", color:"black",position: "absolute", right: "30%", margin:"5px 0px 0px 0px"}} type="submit" id="base"  onClick={() => openInNewTab('/')} ><h6><b>{fname}</b></h6> </button>
      <button style={{width:"250px", height:"40px", boxShadow: "2px 2px 2px 1px #808080", border: "1px solid black", backgroundColor:"#e7e7e7",color:"black", position: "absolute", right: "20%", margin:"105px 0px 0px 0px",color:"black"}}type="submit" id="candidate"  onClick={() => openInNewTab('/')}  ><h6><b>Candidate Generation</b></h6></button>
      <button style={{width:"250px",height:"40px",boxShadow: "2px 2px 2px 1px #808080", border: "1px solid black", backgroundColor:"#e7e7e7",color:"black", position: "absolute", right: "20%", margin:"205px 0px 0px 0px",color:"black"}}type="submit" id="profiling"  onClick={() => openInNewTab('/')}  ><h6><b>Data Profiling</b></h6></button>
      <button style={{ width:"250px",height:"40px",boxShadow: "2px 2px 2px 1px #808080", border: "1px solid black", backgroundColor:"#e7e7e7",color:"black", position: "absolute", right: "20%", margin:"305px 0px 0px 0px",color:"black"}}type="submit" id="clusters"  onClick={() => openInNewTab('/')}  ><h6><b>Clustering</b></h6> </button>
      <button style={{ width:"250px",height:"40px", boxShadow: "2px 2px 2px 1px #808080", border: "1px solid black", backgroundColor:"#e7e7e7",color:"black", position: "absolute", right: "10%", margin:"405px 0px 0px 0px",color:"black"}}type="submit" id="quality"  onClick={() => openInNewTab('/')}  ><h6><b><center>Quality score estimation</center></b></h6> </button>
      <button style={{ width:"250px",height:"40px", boxShadow: "2px 2px 2px 1px #808080", border: "1px solid black", backgroundColor:"#e7e7e7",color:"black", position: "absolute", right: "30%", margin:"405px 0px 0px 0px",color:"black"}}type="submit" id="group"  onClick={() => openInNewTab('/')}  ><h6><b><center>Group selection</center></b></h6> </button>
      <button style={{ width:"250px",height:"40px", boxShadow: "2px 2px 2px 1px #808080", border: "1px solid black", backgroundColor:"#e7e7e7",color:"black", position: "absolute", right: "20%", margin:"505px 0px 0px 0px",color:"black"}}type="submit" id="query"  onClick={() => openInNewTab('/')}  ><h6><b><center>Query selection</center></b></h6> </button>
    <Xarrow
          start="index" //can be react ref
          end="candidate"
          path="straight" //or an id
          color="black"
      />
      <Xarrow
          start="base" //can be react ref
          end="candidate"
          path="straight" //or an id
          color="black"
      />
      
      <Xarrow
          start="candidate" //can be react ref
          end="profiling"
          path="straight" //or an id
          color="black"
      />
         <Xarrow
          start="profiling" //can be react ref
          end="clusters"
          path="straight" //or an id
          color="black"
      />
      <Xarrow
          start="clusters" //can be react ref
          end="quality"
          color="black"
      />
      <Xarrow
          start="clusters" //can be react ref
          end="group"
          color="black"
      />
      <Xarrow
          start="quality" //can be react ref
          end="query"
          path="straight" //or an id
          color="black"
      />
      <Xarrow
          start="group" //can be react ref
          end="query"
          path="straight" //or an id
          color="black"
      />
      
    </div>
  );
}
//export default Apptest
//<a href="/"><img className="photo" src={require('/Users/sainyam/Documents/Metam/src/images/download.jpeg')}></img></a>

//<ReactDiagram
 //       initDiagram={initDiagram}
 //       divClassName='diagram-component'
 //       nodeDataArray={[
 //         { key: 0, category:"before", text: 'Upload dataset', color: color1, loc: '-100 0' },
 //         //type:"https://thumbs.dreamstime.com/b/download-csv-file-group-people-document-isometric-vector-icon-251333552.jpg"
 //         //{ key: 0, category:"after",type:"https://hips.hearstapps.com/hmg-prod.s3.amazonaws.com/images/cute-cat-photos-1593441022.jpg?crop=0.669xw:1.00xh;0.166xw,0&resize=640:*", text: 'Alpha', color: 'lightblue', loc: '0 0' },
 //         { key: 1, category:"before", text: 'Specify Task', color: color2, loc: '50 0' },
 //         { key: 2, category:"before", text: 'Specify external Data', color: color3, loc: '200 0' },
 //         { key: 3, category:"before", text: 'Inspect and Download Results', color: color4, loc: '450 0' }
 //               ]}
 //       linkDataArray={[
//        { from: 0, to: 1 },
  //        { key: 2, from: 1, to: 2 },
  //        { key: 3, from: 2, to: 3 },
  //      ]}
  //     //onModelChange={handleModelChange}
  //    />