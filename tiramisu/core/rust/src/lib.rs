use crc32fast;
use infer;
use jwalk::WalkDirGeneric;
use maplit;
use pyo3::prelude::*;
use sha256::try_digest;
use std::env;
use std::ffi::OsStr;
use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::str;
use std::collections::HashSet;

/// Available error types in Tiramisu digestion phase
///
/// NotFound refers to when a document/file is not found in the filesystem
/// PermissionDenied refers to when the operation cannot be performed due to permission errors
/// CatchAll is all other error types
enum TiramisuErrorType {
    NotFound,
    PermissionDenied,
    CatchAll,
}

/// Struct that contains the Tiramisu Error enum
struct TiramisuError {
    error: TiramisuErrorType,
}

/// Struct to contain the metadata of files ingesting
///
/// tiramisu_path refers to the path relative to the Tiramisu location (e.g. /tiramisu/____)
/// original_path refers to the actual path inside the filesystem
/// file_hash is provided by using SHA256 hash function of the ingested file in binary form
struct TiramisuRecord {
    name: String,
    node_id: String,
    tiramisu_path: String,
    file_extension: String,
    original_path: String,
    node_type: String,
    file_hash: String,
}

// Struct to contain the relationship between two objects
struct RelationshipRecord {
    relationship: String,
    parent: String,
    child: String,
}

// Struct to contain all relationships and objects
struct Dataset {
    folders: Vec<TiramisuRecord>,
    files: Vec<TiramisuRecord>,
    relationships: Vec<RelationshipRecord>,
}

/// Throw Tiramisu errors during parallel walking of filesystem
///
/// If the file type is not one that we specifically list (see below), throw NotFound error
fn jwalk_err_not_found(err: jwalk::Error) -> TiramisuError {
    if let Some(inner) = err.io_error() {
        match inner.kind() {
            io::ErrorKind::InvalidData => TiramisuError {
                error: TiramisuErrorType::NotFound,
            },
            io::ErrorKind::PermissionDenied => TiramisuError {
                error: TiramisuErrorType::PermissionDenied,
            },
            _ => TiramisuError {
                error: TiramisuErrorType::CatchAll,
            },
        }
    } else {
        TiramisuError {
            error: TiramisuErrorType::CatchAll,
        }
    }
}

/// Hash the file by ingesting the file in binary form and creating a SHA256 cryptographic string
fn hash_file(path: &PathBuf) -> String {
    let result = try_digest(path.as_path());
    match result {
        Ok(e) => e,
        Err(p) => p.to_string(),
    }
}

/// Lock all files as readonly to promote preservation and avoid accidental changes
fn set_readonly(path: PathBuf) {
    let metadata = path.metadata().unwrap();
    let mut permissions = metadata.permissions();

    permissions.set_readonly(true);
}

/// Unique ID for each file object is created by using the SHA256 of the file and the path
/// idea is that we wouldn't have two duplicated file in both content and name
/// ensures unique ID for all filesystem objects
fn assign_node_id(hash: &String, path: &PathBuf) -> String {
    let node_id = crc32fast::hash(hash.as_bytes()).to_owned();

    let path_id = crc32fast::hash(path.to_str().unwrap().as_bytes());

    // two identifiers are joined by "+++"
    node_id.to_string() + "+++" + &path_id.to_string()
}

/// Unique ID for each folder object is cated by using the depth and the SHA256 of the path
/// idea is that there won't be a folder with duplicated names at the same level
/// ensures unique ID for all filesystem folders
fn assign_folder_id(depth: &String, path: &PathBuf) -> String {
    let path_id = crc32fast::hash(path.to_str().unwrap().as_bytes());

    depth.to_string() + "+++" + &path_id.to_string()
}

/// Find the depth of the file object
fn calculate_depth(path: &PathBuf) -> usize {
    let mut depth: usize = 0;
    for _ in path.ancestors() {
        depth = depth + 1
    }
    depth
}

/// Remove whitespaces inside a string
fn remove_whitespace(s: &mut String) {
    s.retain(|c| !c.is_whitespace());
}

/// Change the filename on the filesystem
fn change_file_name(path: impl AsRef<Path>, name: &str, new_extension: &str) -> PathBuf {
    let path = path.as_ref();
    let mut result = path.to_owned();
    result.set_file_name(name);
    result.set_extension(new_extension);
    result
}

/// Main digest function to walk through all of the folders and create Tiramisu objects
/// 
/// keep track of all files and relationships to be exported to a graph database
/// tiramisu files with renamed unique IDs are copied to /tiramisu/.tiramisu/____tiramisu_versions
#[pyfunction]
fn digest(core_path_string: String, blacklist: Vec<String>, hidden: bool) -> PyResult<bool> {
    println!("{:?}", env::current_dir().unwrap());

    let mut csv_frame: Dataset = Dataset {
        files: Vec::new(),
        folders: Vec::new(),
        relationships: Vec::new(),
    };
    
    let core_path = PathBuf::from(core_path_string);
    
    let tiramisu_path = core_path
        .clone()
        .join(".tiramisu")
        .join("___tiramisu_versions");

    match core_path.canonicalize() {
        Ok(e) => println!("{} is the path", e.to_str().unwrap()),
        Err(e) => println!("{} is the error", e),
    }

    if !core_path.join(".tiramisu").exists() {
        match fs::create_dir(core_path.join(".tiramisu")) {
            Ok(_) => println!(".tiramisu created"),
            Err(e) => println!("{} error in making", e),
        }
    }

    if !core_path
        .join(".tiramisu")
        .join("___tiramisu_versions")
        .exists()
    {
        match fs::create_dir(core_path.join(".tiramisu").join("___tiramisu_versions")) {
            Ok(_) => println!("tiramisu_versions created"),
            Err(e) => println!("{} error in making", e),
        }
    }
    
    // The current magic library confuses deprecated word/xls/ppt documents with each other. we will put them outside the key so that they are separated.
    // Filetypes in this hashmap are renamed to those file suffixes
    let map = maplit::hashmap! {
        // "application/msword" => "doc",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document" => "docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.template" => "dotx",
        // "application/vnd.ms-excel" => "xls",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" => "xlsx",
        // "application/vnd.ms-powerpoint" => "ppt",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation" => "pptx",
        "text/csv" => "csv",
        "application/gzip" =>"gz",
        "image/gif" => "gif",
        "text/html" => "html",
        "image/jpeg" => "jpeg",
        "application/json" => "json",
        "video/mp4" => "mp4",
        "video/mpeg" => "mpeg",
        "audio/mpeg" => "mp3",
        "image/png" =>"png",
        "application/pdf" => "pdf",
        "application/vnd.rar" => "rar",
        "application/rtf" => "rtf",
        "image/svg+xml" => "svg",
        "application/x-tar" => "tar",
        "image/tiff" => "tiff",
        "text/plain" => "txt",
        "text/rtf" => "rtf",
        "image/webp" => "webp",
        "application/xml" => "xml",
        "application/zip" => "zip",
        "application/x-7z-compressed" => "7z",
        "application/x-xz" => "tar.xz"
    };

    // Use the jwalk library for parallel ingestion
    // https://github.com/Byron/jwalk
    // We skip hidden files
    let walk_dir = WalkDirGeneric::<(usize, bool)>::new(core_path.clone())
        .skip_hidden(hidden)
        .process_read_dir(move |_depth, _path, _read_dir_state, children| {
            children.iter_mut().for_each(|dir_entry_result| {
                if let Ok(dir_entry) = dir_entry_result {
                    let temp_metadata = dir_entry.metadata();

                    let metadata = match temp_metadata {
                        Ok(file) => file.is_dir(),
                        Err(error) => match jwalk_err_not_found(error).error {
                            TiramisuErrorType::NotFound => false,
                            TiramisuErrorType::PermissionDenied => false,
                            TiramisuErrorType::CatchAll => false,
                        },
                    };

                    // avoid reading any children files under folders that are blacklisted
                    if metadata {
                        if blacklist
                            .iter()
                            .any(|e| dir_entry.path().to_str().unwrap() == e.to_owned())
                        {
                            dir_entry.read_children_path = None;
                        }
                    }
                }
            });
            children.retain(|dir_entry_result| {
                dir_entry_result
                    .as_ref()
                    .map(|dir_entry| {
                        let path = dir_entry.path();
                        let utf_path = path.extension().unwrap_or(OsStr::new("")).to_string_lossy();
                        let temp_extension = utf_path.as_ref();
                        match temp_extension {
                            "-" => false,
                            _ => true,
                        }
                    })
                    .unwrap_or(false)
            });
        });

    let root = walk_dir.root();
    
    let mut root_string = String::from(root.to_str().unwrap());

    remove_whitespace(&mut root_string);

    // assign nodeID for file
    let root_hash = hash_file(&PathBuf::from(root));

    let root_node_id = assign_node_id(
        &root_hash,
        &root
            .strip_prefix(core_path.parent().expect(""))
            .unwrap()
            .to_path_buf(),
    );

    
    let root_record = TiramisuRecord {
        name: String::from(PathBuf::from(root).file_name().unwrap().to_str().unwrap()),
        node_id: root_node_id,
        tiramisu_path: root_string,
        original_path: root.to_string_lossy().into_owned(),
        file_extension: String::from("folder"),
        node_type: String::from("Folder"),
        file_hash: String::from("ROOT"),
    };

    csv_frame.folders.push(root_record);
    
    for entry in walk_dir {
        if let Ok(valid) = entry {
            // println!("{:?}", valid.path());
            let valid_path = valid.path();
            let valid_extension = valid_path
                .extension()
                .unwrap_or(OsStr::new(""))
                .to_str()
                .unwrap();
            let valid_filename = valid_path
                .file_name()
                .unwrap_or(OsStr::new(""))
                .to_str()
                .unwrap();
            let correct_extension: String;
            let mut newpath: PathBuf;
            let relationship: String;

            let exceptions: HashSet<_> = ["pptx", "ppt", "xls", "doc", "xlsx", "docx"].iter().cloned().collect();

            // check the magic number signature to ensure that it's supported
            if valid_path.is_file() && valid_filename != "" && (infer::is_supported(valid_extension) || exceptions.contains(valid_extension))
            {
                let final_result;
                let result =
                    infer::get_from_path(valid_path.as_path()).expect("file read successfully");

                if let None = result {
                    println!("skipping {}", valid_filename);
                } else {
                    final_result = result.expect("");
                    if map.contains_key(final_result.mime_type()) {
                        let matched = match map.get(final_result.mime_type()) {
                            Some(s) => s,
                            None => "",
                        };

                        // if the detected extension is not what it was named, either rename with the correct extension
                        // or leave it as is (docx, pptx, and xlsx will fall here)
                        if matched != valid_extension {
                            
                            // correct extension
                            correct_extension =
                                map.get(final_result.mime_type()).unwrap().to_string();
                            newpath = PathBuf::from(valid_filename);
                            newpath = change_file_name(newpath, valid_filename, &correct_extension);
                        } else {
                            correct_extension = valid_extension.to_string();
                            newpath = PathBuf::from(valid_filename);
                        }
                    } else {
                        println!("{} is not part of the valid set of extensions. Not checking for correction. ", final_result.mime_type());
                        correct_extension = valid_extension.to_string();
                        newpath = PathBuf::from(valid_filename);
                    }
                    let mut owned_string = newpath.into_os_string().into_string().unwrap();
                    // strip whitespace from filepath
                    remove_whitespace(&mut owned_string);

                    // assign nodeID for file
                    let hash = hash_file(&valid_path);

                    let node_id = assign_node_id(
                        &hash,
                        &valid_path
                            .strip_prefix(core_path.parent().expect(""))
                            .unwrap()
                            .to_path_buf(),
                    );

                    // make nodeID folder in tiramisu versions
                    if !tiramisu_path.join(&node_id).exists() {
                        match fs::create_dir(tiramisu_path.join(&node_id)) {
                            Ok(_) => println!("{} digested", valid_path.to_str().unwrap()),
                            Err(e) => println!("{} error in making {}", e, node_id),
                        }
                    }

                    let full_tiramisu_path = tiramisu_path.join(&node_id).join(&owned_string);
                    // copy file to tiramisu versions with new nodeID
                    let _ = fs::copy(&valid_path, &full_tiramisu_path);

                    // lock files in read_only

                    set_readonly(tiramisu_path.join(&node_id).join(&owned_string));

                    // get the nodeID of the parent folder
                    let mut parent_path = valid_path
                        .parent()
                        .unwrap()
                        .strip_prefix(core_path.parent().expect(""))
                        .unwrap()
                        .to_path_buf()
                        .into_os_string()
                        .into_string()
                        .unwrap();
                    remove_whitespace(&mut parent_path);
                    let parent_depth =
                        calculate_depth(&PathBuf::from(valid_path.parent().unwrap())).to_string();
                    let parent_node_id =
                        assign_folder_id(&parent_depth, &PathBuf::from(parent_path));

                    // all relationships are "CONTAINS" for folder-file
                    // deprecated, but leaving here for debugging purposes
                    relationship = String::from("CONTAINS");
                    
                    // save into dataset records
                    let temp_record = TiramisuRecord {
                        name: String::from(
                            PathBuf::from(&owned_string)
                                .file_name()
                                .unwrap()
                                .to_str()
                                .unwrap(),
                        ),
                        node_id: node_id.clone(),
                        tiramisu_path: full_tiramisu_path.to_string_lossy().into_owned(),
                        original_path: valid_path.as_path().to_string_lossy().into_owned(),
                        file_extension: correct_extension.to_string(),
                        node_type: String::from("File"),
                        file_hash: hash,
                        // parent_node_id: parent_node_id,
                        // relationship: relationship,
                    };

                    let relationship_record = RelationshipRecord {
                        relationship: relationship,
                        parent: parent_node_id,
                        child: node_id,
                    };

                    csv_frame.files.push(temp_record);
                    csv_frame.relationships.push(relationship_record);
                }
                
                // if corrected, and combined_to relationships
            } else if valid_path.is_dir() && valid_filename != "" {
                let mut parent_path = valid_path
                    .parent()
                    .unwrap()
                    .strip_prefix(core_path.parent().expect(""))
                    .unwrap()
                    .to_path_buf()
                    .into_os_string()
                    .into_string()
                    .unwrap();
                remove_whitespace(&mut parent_path);
                let parent_depth =
                    calculate_depth(&PathBuf::from(valid_path.parent().unwrap())).to_string();
                let parent_node_id = assign_folder_id(&parent_depth, &PathBuf::from(&parent_path));

                let mut node_path = valid_path
                    .strip_prefix(core_path.parent().expect(""))
                    .unwrap()
                    .to_path_buf()
                    .into_os_string()
                    .into_string()
                    .unwrap();
                remove_whitespace(&mut node_path);
                let node_depth = calculate_depth(&valid_path).to_string();
                let node_id = assign_folder_id(&node_depth, &PathBuf::from(&node_path));
                // strip whitespace from folder name
                // assign nodeID for folder based on depth and name
                // save into dataset records
                relationship = String::from("CONTAINS");

                let temp_record = TiramisuRecord {
                    name: String::from(
                        PathBuf::from(&node_path)
                            .file_name()
                            .unwrap()
                            .to_str()
                            .unwrap(),
                    ),
                    node_id: node_id.clone(),
                    tiramisu_path: node_path,
                    original_path: valid_path.as_path().to_string_lossy().into_owned(),
                    file_extension: String::from("folder"),
                    node_type: String::from("Folder"),
                    file_hash: node_depth,
                    // parent_node_id: parent_node_id,
                    // relationship: relationship,
                };

                let relationship_record = RelationshipRecord {
                    relationship: relationship,
                    parent: parent_node_id,
                    child: node_id,
                };

                csv_frame.folders.push(temp_record);
                csv_frame.relationships.push(relationship_record);
            }
        }
    }

    // take advantage of Neo4J's bulk data import
    let mut wtr = csv::Writer::from_path(
        core_path
            .join(".tiramisu")
            .join("neo4j")
            .join("import")
            .join("files.csv"),
    )
    .unwrap();
    let mut folders = csv::Writer::from_path(
        core_path
            .join(".tiramisu")
            .join("neo4j")
            .join("import")
            .join("folders.csv"),
    )
    .unwrap();
    let mut relationships = csv::Writer::from_path(
        core_path
            .join(".tiramisu")
            .join("neo4j")
            .join("import")
            .join("relationships.csv"),
    )
    .unwrap();

    match wtr.write_record(&[
        "Name",
        "NodeID",
        "TiramisuPath",
        "OriginalPath",
        "FileExtension",
        "NodeType",
        "FileHash",

    ]) {
        Ok(_) => println!("Saved to CSV"),
        Err(error) => println!("{}", error),
    };
    for (_, row) in csv_frame.files.into_iter().enumerate() {
            match wtr.serialize((
                row.name,
                row.node_id,
                row.tiramisu_path,
                row.original_path,
                row.file_extension,
                row.node_type,
                row.file_hash,

            )) {
                Ok(_) => (),
                Err(error) => println!("{} error in row", error),
            };
    }
    wtr.flush()?;

    match folders.write_record(&[
        "Name",
        "NodeID",
        "TiramisuPath",
        "OriginalPath",
        "FileExtension",
        "NodeType",
        "FileHash",
    ]) {
        Ok(_) => println!("Saved to CSV"),
        Err(error) => println!("{}", error),
    };
    for (i, row) in csv_frame.folders.into_iter().enumerate() {
        if i > 0 {
            match folders.serialize((
                row.name,
                row.node_id,
                row.tiramisu_path,
                row.original_path,
                row.file_extension,
                row.node_type,
                row.file_hash,

            )) {
                Ok(_) => (),
                Err(error) => println!("{} error in row", error),
            };
        }
    }
    folders.flush()?;

    match relationships.write_record(&[
        "Relationship",
        "Parent",
        "Child",

    ]) {
        Ok(_) => println!("Saved to CSV"),
        Err(error) => println!("{}", error),
    };
    for (i, row) in csv_frame.relationships.into_iter().enumerate() {
        if i > 0 {
            match relationships.serialize((
                row.relationship,
                row.parent,
                row.child,

            )) {
                Ok(_) => (),
                Err(error) => println!("{} error in row", error),
            };
        }
    }
    relationships.flush()?;
    Ok(true)
}

#[pymodule]
fn tiramisu_digest(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(digest, m)?)?;
    Ok(())
}