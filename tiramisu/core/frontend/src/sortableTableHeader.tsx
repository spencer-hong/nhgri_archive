import { TableCell, TableHead, TableRow } from "@material-ui/core";


export const SortableHeader = () => {
    return (
        <TableHead>
            <TableRow>
                <TableCell>Action</TableCell>
                <TableCell>Files Affected</TableCell>
                <TableCell>Description of Task</TableCell>
                <TableCell>Extra Parameters</TableCell>
            </TableRow>
        </TableHead>
    );
};