import "./index.css"

const TablePreview = ({ preview,colorlst }) => {

    if (preview) {
        return <div className="container_preview">
        <table className="u-max-full-width tablepreview_text">

        <thead> 
          <tr>
            {
              Object.keys(preview[0]).map(column_name => {
                 if (colorlst.includes(column_name)) {
                  return <th bgcolor="red" key={column_name}>{column_name}</th>
                }
                  else{
                 return <th bgcolor="#E8E8E8" key={column_name}>{column_name}</th>
                  }
                }
              )
            }
          </tr>
        </thead>

        <tbody>
        
          {
            preview.map(row => {
              return <tr>
                {
                  Object.keys(row).map(element => {
                    if (colorlst.includes(row[element])) {
                    return <td bgcolor="red">
                      {row[element]}
                    </td>
                    }
                    else{
                      return <td>
                      {row[element]}
                    </td>
                    }
                    }
                  )
                }
              </tr>
            })
          }

        </tbody>
      </table>
      </div>
    }
}

export default TablePreview;