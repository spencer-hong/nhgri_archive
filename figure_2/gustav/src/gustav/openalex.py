import os
import pandas as pd

from gustav import inout


def authors(columns=None, filters=None):
    """
    Import information related to authors:
    
    ['author_id', 'display_name', 'orcid', 'works_count']

    Input:
    columns: list of columns to use (add non-included column to see all options)
    filters: dictionary with column as key and permitted parameters as values/list, 
            e.g.: filters={'institution_id': [list of allowed ids]}
    """

    df = _from_split_parquets(
        data_category='authors', 
        medline_category=None, 
        columns=columns, 
        filters=filters) 

    return df


def institutions(dataset='main', columns=None, filters=None):
    """
    Import information related to institutions:
    
    main: ['concept_id', 'display_name', 'level', 'description', 'ancestors']
    relationships: ['institution_id', 'related_institution_id', 'relationship']

    Input:
    dataset: main, 
    columns: list of columns to use (add non-included column to see all options)
    filters: dictionary with column as key and permitted parameters as values/list, 
            e.g.: filters={'institution_id': [list of allowed ids]}
    """


    data_version = inout.get_data_version('openalex')

    p = 'openalex/{}/institutions_{}.parquet'.format(data_version, dataset)
    df = _from_single_parquet(p, columns, filters)

    return df

    
def concepts(columns=None, filters=None):
    """
    Import information related to concepts:
        ['concept_id', 'display_name', 'level', 'description', 'ancestors']

    Input:
    columns: list of columns to use (add non-included column to see all options)
    filters: dictionary with column as key and permitted parameters as values/list, 
            e.g.: filters={'concept_id': [list of allowed ids]}
    """

    data_version = inout.get_data_version('openalex')

    p = 'openalex/{}/concepts.parquet'.format(data_version)
    df = _from_single_parquet(p, columns, filters)

    return df


def publishers(columns=None, filters=None):
    """
    Import information related to publishers:
       ['publisher_id', 'display_name', 'works_count', 'hierarchy_level',
       'parent_id']

    Input:
    columns: list of columns to use (add non-included column to see all options)
    filters: dictionary with column as key and permitted parameters as values/list, 
            e.g.: filters={'publisher_id': [list of allowed ids]}
    """


    data_version = inout.get_data_version('openalex')

    p = 'openalex/{}/publishers.parquet'.format(data_version)
    df = _from_single_parquet(p, columns, filters)

    return df



def sources(dataset='main', columns=None, filters=None):
    """
    Import information related to sources (such as journals)

    Major categories:
    main: ['source_id', 'display_name', 'type', 'abbreviated_title', 'issn',
       'issn_l', 'works_count', 'cited_by_count', 'country_code',
       'homepage_url', 'host_organization_id', 'host_organization_name',
       'alternate_titles']
    by_year: ['source_id', 'year', 'works_count', 'cited_by_count']


    Input:
    datasets: main, by_year
    columns: list of columns to use (add non-included column to see all options)
    filters: dictionary with column as key and permitted parameters as values/list, 
            e.g.: filters={'source_id': [list of allowed ids]}
    """

    data_version = inout.get_data_version('openalex')

    p = 'openalex/{}/sources_{}.parquet'.format(data_version, dataset)
    df = _from_single_parquet(p, columns, filters)

    return df
    

def works(dataset='main', medline_category=None, columns=None, filters=None):
    """
    Import information related to works. Major categories:

    main: primary information about publication; ['work_id', 'source_id', 'doi', 
        'year', 'title', 'type', 'is_retracted','pubmed_id']
    citations: citing and referenced papers (encoded by work_id)
    concepts: concepts mapped by OpenAlex to works
    authors: ['work_id', 'author_id', 'author_position', 'author_number', 'is_corresponding']

    Input:
    datasets: authors, citations, concepts, publications
    medline_category: pubmed_id, pmc_id, neither; alternatively set leave at default (None) to consider all
    columns: list of columns to use (add non-included column to see all options)
    filters: dictionary with column as key and permitted parameters as values/list, 
            e.g.: filters={'work_id': [list of allowed ids]}
    """

   
    
    # if columns:
    #     columns = [x.replace('source_id', 'venue_id') for x in columns]
    # if filters:
    #     if 'source_id' in filters.keys():
    #         filters['venue_id'] = filters.pop('source_id')
        
    def _get_for_one_medline_category(dataset, medline_category, columns, filters):
        
        df = _from_split_parquets(
            data_category=f'works_{dataset}', 
            medline_category=f'has_{medline_category}', 
            columns=columns, 
            filters=filters)
        # df = df.rename(columns={'venue_id': 'source_id'})
        return df

    if medline_category is None:
        agg = []
        for category in ['pubmed_id', 'pmc_id', 'neither']:
            df = _get_for_one_medline_category(
                dataset, category, columns, filters)
            agg.append(df)
        df = pd.concat(agg)    
    else:
         df = _get_for_one_medline_category(
                dataset, medline_category, columns, filters)   
  
    return df



def _from_single_parquet(p, columns=None, filters=None):
    df = pd.read_parquet(
        inout.get_input_path(p), columns=columns)

    if filters:
        for key in filters.keys():
            df = df.loc[df.loc[:, key].isin(filters[key]), :] 
    return df


def _from_split_parquets(data_category, medline_category=None, columns=None, filters=None):

    data_version = inout.get_data_version('openalex')

    p = 'openalex/{}'.format(data_version)
    openalex_folder = inout.get_input_path(p)

    if medline_category:
        basedir =  os.path.join(openalex_folder, data_category, medline_category)
    else:
        basedir =  os.path.join(openalex_folder, data_category)


    agg = []
    for subfolder in sorted([f.path for f in os.scandir(basedir) if f.is_dir()]):

        files = [f for f in os.listdir(subfolder) if os.path.isfile(os.path.join(subfolder, f))]
        files = [os.path.join(subfolder, x) for x in files if x.endswith('.parquet')]

        for file in files:
            df = _from_single_parquet(file, columns=columns, filters=filters)

            agg.append(df)

    df = pd.concat(agg).drop_duplicates()

    return df