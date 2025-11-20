const { createContext } = require("react");

const FormDataCtxt = createContext({
    formData: {},
    setFormData: () => {}
});

export default FormDataCtxt;