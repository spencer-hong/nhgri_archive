use pyo3::prelude::*;


#[pyfunction]
fn _sliding_window(_py: Python, words: Vec<String>, window_size: usize, overlap_size: usize)
    -> PyResult<Vec<Vec<String>>>
{
    let mut result = Vec::new();
    if words.len() <= window_size {
        result.push(words)
    }
    else {
    
    let mut start = 0;

    while start + window_size <= words.len() {
        let end = start + window_size;
        let window: Vec<String> = words[start..end].to_vec();
        result.push(window);

        start += window_size - overlap_size;
    }
    let window: Vec<String> = words[start - overlap_size - overlap_size..words.len()].to_vec();
    result.push(window);

   
}
 Ok(result)
}


// #[pyfunction]
// fn _sliding_window(words: Vec<String>, window_size: usize, overlap_size:usize) -> Vec<Vec<String>> {
// }

#[pymodule]
fn rust_utils(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(_sliding_window, m)?)?;
    Ok(())
}