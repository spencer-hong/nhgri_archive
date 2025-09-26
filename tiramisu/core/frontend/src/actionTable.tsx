import {
  Button,
  TableBody,
  TableCell,
  TableRow,
  TextField,
} from "@material-ui/core";
import { makeStyles } from "@material-ui/core/styles";
import MaterialTable from "@material-ui/core/Table";
import { useState } from "react";
import { TSMap } from "typescript-map";
import { fetchData } from "./actionTableData";
import postData from "./postData";
import { SortableHeader } from "./sortableTableHeader";

const useStyles = makeStyles({
  table: {
    width: "100%",
    height: "100%",
  },
});

interface DataItem {
  key: string;
  action:  string|Record<string, string>;
  namespace: string;
  description: string;
  chain: boolean;
  kwargs?: Record<string, any>;
  parameters?: string[];
}

const ActionTable: React.FC = () => {
  const dataList: DataItem[] = fetchData();
  const [paramValues, setParamValues] = useState<Record<string, Record<string, string>>>({});
  const classes = useStyles();

  const handleInputChange = (key: string, param: string, value: string) => {
    setParamValues((prev) => ({
      ...prev,
      [key]: {
        ...prev[key],
        [param]: value,
      },
    }));
  };

  return (
    <div>
      <MaterialTable className={classes.table}>
        <SortableHeader />
        <TableBody>
          {dataList.map((data, i) => {
            return (
              <TableRow key={i}>
                <TableCell>
                  <Button
                    variant="contained"
                    color="primary"
                    onClick={() => {
                      let kwargs_send = new TSMap<string, any>();
                      if (data.kwargs) {
                        kwargs_send = new TSMap(Object.entries(data.kwargs));
                      }
                      
                      // Merge user-inputted parameters
                      if (paramValues[data.key]) {
                        Object.entries(paramValues[data.key]).forEach(([k, v]) => {
                          kwargs_send.set(k, v);
                        });
                      }
                      
                      postData(data.key, kwargs_send, data.chain);
                    }}
                  >
                    {data.action}
                  </Button>
                </TableCell>
                <TableCell>{data.namespace}</TableCell>
                <TableCell>{data.description}</TableCell>
                <TableCell>
                  {data.parameters?.map((param, index) => (
                    <TextField
                      key={index}
                      label={param}
                      variant="outlined"
                      size="small"
                      onChange={(e) => handleInputChange(data.key, param, e.target.value)}
                      style={{ marginRight: 8 }}
                    />
                  ))}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </MaterialTable>
    </div>
  );
};

export default ActionTable;