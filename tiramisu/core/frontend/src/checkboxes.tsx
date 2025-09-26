import Checkbox from "@material-ui/core/Checkbox";
import FormControlLabel from "@material-ui/core/FormControlLabel";

const Checkboxes = () => {
  return (
    <div>
      <FormControlLabel control={<Checkbox defaultChecked />} label="PDFs" />
      <FormControlLabel control={<Checkbox defaultChecked />} label="Docxs" />
    </div>
  );
};

export default Checkboxes;
