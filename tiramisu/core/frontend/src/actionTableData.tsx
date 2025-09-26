// Send actions from buttons by specifying the Tiramisu action in "action" and the arguments in "kwargs"
interface TableData {
  action: string|Record<string, string>;
  namespace: Namespace;
  description: string;
  key: string;
  chain: boolean
  kwargs: any;
  parameters: string[];
}

// Specify namespace for buttons
enum Namespace {
  images = "Images",
  pdfs = "PDFs",
  ms_office = "MS Office",
  ms_word = "MS Word",
  text = "Text",
  all = "All",
  none = "None",
}

// Types of actions configurable through button on the homepage
const dataList = [
  // Send "start_digest" to Celery through this button
  {
    action: "Digest",
    namespace: Namespace.all,
    key: "start_digest",
    description:
      "Prepare Tiramisu by digesting all of the applicable content in the specified corpus. A necessary first step.",
    kwargs: null,
    chain: false,
  },
  {
    action: "Convert MS to PDFs",
    namespace: Namespace.ms_word,
    key: [
      {"action": "doc_to_pdf_supervisor_digest"}, 
      {"action": "docx_to_pdf_supervisor_digest"},
      ],
    description:
    "Process MS documents by converting to PDFs",
    kwargs: null,
    chain: true,
  },
  {
    action: "Split PDFs",
    namespace: Namespace.ms_word,
    key: [
      {"action": "split_pdfs_supervisor_digest"}, 
      ],
    description:
    "Determine if a PDF is scanned or born-digital",
    kwargs: null,
    chain: true,
  },
  {
    action: "Determine type of PDF",
    namespace: Namespace.ms_word,
    key: [
      {"action": "find_pdf_type_supervisor_digest"}, 
      ],
    description:
    "Determine if a PDF is scanned or born-digital",
    kwargs: null,
    chain: true,
  },
  {
    action: "Convert PDF to images",
    namespace: Namespace.ms_word,
    key: [
      {"action": "pdf_to_image_supervisor_digest"}, 
      ],
    description:
    "Convert PDFs to images",
    kwargs: null,
    chain: true,
  },
  {
    action: "Visualize a specific PDF or image",
    namespace: Namespace.pdfs,
    key: "show_me_in_labelstudio",
    description: "Pull up a specific file from Tiramisu using LabelStudio.",
    kwargs: {
      "query":  "match (d:File) where d.nodeID = \"{nodeID}\" return d.nodeID as nodeID, d.tiramisuPath as file, d.fileExtension as extension, d.originalPath as originalPath",
      "title": "visualize {nodeID}",
        },
    chain: false,
    parameters: ["api", "nodeID", "configuration"]
  },
  {
    action: "Upload a corpus to LabelStudio",
    namespace: Namespace.all,
    key: "upload_to_labelstudio",
    kwargs: null,
    description: "Upload a corpus (in JSONL format) to LabelStudio to label",
    chain: false,
    parameters: ["jsonl", "api", "title", "configuration"]
  }
] as TableData[];

export const fetchData = () => {
  return dataList;
};
