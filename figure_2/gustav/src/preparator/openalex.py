import gzip
import json
import os

import numpy as np
import pandas as pd

from preparator import inout


# openalex_folder = '/Users/tstoeger/outside_time_machine/openalex/2023-02-27/data'

# openalex_folder_out = '/Users/tstoeger/Desktop/tmp'



def authors():

    entity = 'authors'

    data_version = inout.get_data_version('openalex')
    basedir = inout.get_input_path(
        'manual/openalex/{}/data/{}'.format(
            data_version, entity
        ), big=True)


    letter = entity[0].upper()

    forbidden_ids = _get_merged_ids(entity)



    folders = [f.path for f in os.scandir(basedir) if f.is_dir()]
    folders_in_order_to_process = sorted(folders)[::-1]    # https://docs.openalex.org/download-all-data/snapshot-data-format

    for subfolder in folders_in_order_to_process:    

        files = [f for f in os.listdir(subfolder) if os.path.isfile(os.path.join(subfolder, f))]
        files = [os.path.join(subfolder, x) for x in files if x.endswith('.gz')]

        for file in files:
            
            
            authors = []
            shortened_file_path = os.sep.join(file.split(os.sep)[-2:])

            with gzip.open(file, 'rt', encoding='UTF-8') as zipfile:
                for line in zipfile:
                    entry = json.loads(line)

                    entry_id = _safely_establish_id(entry['id'], letter)

                    if entry_id in forbidden_ids:
                        continue
                    elif entry_id is not None:
                        forbidden_ids.add(entry_id)

                    if entry['orcid']:
                        orcid = entry['orcid'].replace('https://orcid.org/', '')
                    else:
                        orcid = entry['orcid']
                                                
                    record = {
                        'author_id': entry_id,
                        'display_name': entry['display_name'],
                        'orcid': orcid,
                        'works_count': int(entry['works_count'])

                    }
                    authors.append(record)
                
                
            if len(authors)>0:
                d = pd.DataFrame(authors).sort_values('author_id')
                p = 'openalex/{}/authors/{}'.format(
                    data_version,
                    shortened_file_path.replace('.gz', '.parquet')
                    )
                inout.export_plain_table(d, p)



def concepts():

    entity = 'concepts'

    data_version = inout.get_data_version('openalex')
    basedir = inout.get_input_path(
        'manual/openalex/{}/data/{}'.format(
            data_version, entity
        ), big=True)



    letter = entity[0].upper()

    forbidden_ids = set() #_get_merged_ids(entity)


    concepts = []

    folders = [f.path for f in os.scandir(basedir) if f.is_dir()]
    folders_in_order_to_process = sorted(folders)[::-1]    # https://docs.openalex.org/download-all-data/snapshot-data-format

    for subfolder in folders_in_order_to_process:    

        files = [f for f in os.listdir(subfolder) if os.path.isfile(os.path.join(subfolder, f))]
        files = [os.path.join(subfolder, x) for x in files if x.endswith('.gz')]

        for file in files:
            shortened_file_path = os.sep.join(file.split(os.sep)[-2:])

            with gzip.open(file, 'rt', encoding='UTF-8') as zipfile:
                for line in zipfile:
                    entry = json.loads(line)

                    entry_id = _safely_establish_id(entry['id'], letter)

                    if entry_id in forbidden_ids:
                        continue
                    elif entry_id is not None:
                        forbidden_ids.add(entry_id)
                    
                    ancestors = [_safely_establish_id(x['id'], 'C') for x in entry['ancestors']]

                    record = {
                        'concept_id': entry_id,
                        'display_name': entry['display_name'],
                        'level': entry['level'],
                        'description': entry['description'],
                        'ancestors': ancestors
                    }
                    concepts.append(record)

    concepts = pd.DataFrame(concepts)

    concepts = concepts.sort_values(by=['concept_id'])

    if concepts['concept_id'].value_counts().max()>1:
        raise AssertionError('Some concept_id is ambiguous')


    p = 'openalex/{}/concepts.parquet'.format(
            data_version,
            )
    # p = os.path.join(openalex_folder_out, 'concepts.parquet')
    inout.export_plain_table(concepts,p)
     


def institutions():

    entity = 'institutions'

    data_version = inout.get_data_version('openalex')
    basedir = inout.get_input_path(
        'manual/openalex/{}/data/{}'.format(
            data_version, entity
        ), big=True)



    letter = entity[0].upper()

    forbidden_ids = _get_merged_ids(entity)


    institutions = []
    relationships = []

    folders = [f.path for f in os.scandir(basedir) if f.is_dir()]
    folders_in_order_to_process = sorted(folders)[::-1]    # https://docs.openalex.org/download-all-data/snapshot-data-format

    for subfolder in folders_in_order_to_process:    

        files = [f for f in os.listdir(subfolder) if os.path.isfile(os.path.join(subfolder, f))]
        files = [os.path.join(subfolder, x) for x in files if x.endswith('.gz')]

        for file in files:
            shortened_file_path = os.sep.join(file.split(os.sep)[-2:])

            with gzip.open(file, 'rt', encoding='UTF-8') as zipfile:
                for line in zipfile:
                    entry = json.loads(line)

                    entry_id = _safely_establish_id(entry['id'], letter)

                    if entry_id in forbidden_ids:
                        continue
                    elif entry_id is not None:
                        forbidden_ids.add(entry_id)

                    if entry['ror']:
                        ror = entry['ror'].replace('https://ror.org/', '')
                    else:
                        ror = None

                    record = {
                        'institution_id': entry_id,
                        'institution_ror': ror,
                        'country_code': entry['country_code'],
                        'type': entry['type'],
                        'display_name': entry['display_name'],
                        'works_count': int(entry['works_count']),
                        'homepage_url': entry['homepage_url'],
                    }
                    institutions.append(record)


                    for associated_institution in entry['associated_institutions']:

                        relation = {
                            'institution_id': entry_id,
                            'related_institution_id': _safely_establish_id(associated_institution['id'], letter),
                            'relationship': associated_institution['relationship']
                        }

                        relationships.append(relation)

    institutions = pd.DataFrame(institutions)
    institutions = institutions.sort_values(by=list(institutions.columns)).drop_duplicates()

    relationships = pd.DataFrame(relationships).drop_duplicates()
    relationships = relationships.sort_values(by=list(relationships.columns)).drop_duplicates()

    if institutions['institution_id'].value_counts().max()>1:
        raise AssertionError('Some institution_id is ambiguous')


    # p = os.path.join(openalex_folder_out, 'institutions_main.parquet')
    p = 'openalex/{}/institutions_main.parquet'.format(
            data_version
            )
    inout.export_plain_table(institutions,p)
     
    # p = os.path.join(openalex_folder_out, 'institutions_relationships.parquet')
    p = 'openalex/{}/institutions_relationships.parquet'.format(
        data_version
        )
    inout.export_plain_table(relationships,p)


def publishers():
    entity = 'publishers'

    data_version = inout.get_data_version('openalex')

    basedir = inout.get_input_path(
        'manual/openalex/{}/data/{}'.format(
            data_version, entity
        ), big=True)



    letter = entity[0].upper()

    forbidden_ids = set() #_get_merged_ids(entity)


    publishers = []


    folders = [f.path for f in os.scandir(basedir) if f.is_dir()]
    folders_in_order_to_process = sorted(folders)[::-1]    # https://docs.openalex.org/download-all-data/snapshot-data-format

    for subfolder in folders_in_order_to_process:    

        files = [f for f in os.listdir(subfolder) if os.path.isfile(os.path.join(subfolder, f))]
        files = [os.path.join(subfolder, x) for x in files if x.endswith('.gz')]

        for file in files:
            shortened_file_path = os.sep.join(file.split(os.sep)[-2:])

            with gzip.open(file, 'rt', encoding='UTF-8') as zipfile:
                for line in zipfile:
                    entry = json.loads(line)

                    entry_id = _safely_establish_id(entry['id'], letter)

                    if entry_id in forbidden_ids:
                        continue
                    elif entry_id is not None:
                        forbidden_ids.add(entry_id)

                    if entry['parent_publisher']:
                        parent = _safely_establish_id(entry['parent_publisher'], letter)
                    else:
                        parent = None

                    record = {
                        'publisher_id': entry_id,
                        'display_name': entry['display_name'],
                        'works_count': int(entry['works_count']),
                        'hierarchy_level': int(entry['hierarchy_level']),
                        'parent_id': parent,
                    }
                    publishers.append(record)


    publishers = pd.DataFrame(publishers)
    publishers = publishers.sort_values(by=['publisher_id']).drop_duplicates()

    
    if publishers['publisher_id'].value_counts().max()>1:
        raise AssertionError('Some publisher_id is ambiguous')

    p = 'openalex/{}/publishers.parquet'.format(
        data_version
        )
    # p = os.path.join(openalex_folder_out, 'publishers.parquet')
    inout.export_plain_table(publishers,p)
     

def sources():

    entity = 'sources'
    # outdir = openalex_folder_out

    data_version = inout.get_data_version('openalex')
    basedir = inout.get_input_path(
        'manual/openalex/{}/data/{}'.format(
            data_version, entity
        ), big=True)



    letter = entity[0].upper()

    forbidden_ids = _get_merged_ids(entity)


    sources = []
    sources_by_year = []

    folders = [f.path for f in os.scandir(basedir) if f.is_dir()]
    folders_in_order_to_process = sorted(folders)[::-1]    # https://docs.openalex.org/download-all-data/snapshot-data-format

    for subfolder in folders_in_order_to_process:    

        files = [f for f in os.listdir(subfolder) if os.path.isfile(os.path.join(subfolder, f))]
        files = [os.path.join(subfolder, x) for x in files if x.endswith('.gz')]

        for file in files:
            shortened_file_path = os.sep.join(file.split(os.sep)[-2:])

            with gzip.open(file, 'rt', encoding='UTF-8') as zipfile:
                for line in zipfile:
                    entry = json.loads(line)

                    entry_id = _safely_establish_id(entry['id'], letter)

                    if entry_id in forbidden_ids:
                        continue
                    elif entry_id is not None:
                        forbidden_ids.add(entry_id)

                    if entry['alternate_titles']:
                        alternative_names = entry['alternate_titles']
                    else:
                        alternative_names = None


                    if entry['host_organization']:
                        host_id = entry['host_organization'].replace('https://openalex.org/', '')
                    else:
                        host_id = None                    

                    record = {
                        'source_id': entry_id,
                        'display_name': entry['display_name'],
                        'type': entry['type'],
                        'abbreviated_title': entry['abbreviated_title'],
                        'issn': entry['issn'],
                        'issn_l': entry['issn'],
                        'works_count': int(entry['works_count']),
                        'cited_by_count': int(entry['cited_by_count']),
                        'country_code': entry['country_code'],
                        'homepage_url': entry['homepage_url'],
                        'host_organization_id': host_id,
                        'host_organization_name': entry['host_organization_name'], # as of 2023-02-27 this has more infomration than id alone
                        # 'publisher': entry['publisher'],    # deprecatres on 2023-03-06, as of 2023-02-27 redudant with host_organization_name
                        'alternate_titles': alternative_names
                    }
                    sources.append(record)


                    if len(entry['counts_by_year'])>0:
                        d = pd.DataFrame(entry['counts_by_year']).set_index('year').reindex(
                            range(2012, 2023)   # openalex only covers last 10 years
                        ).fillna(0).astype(int).reset_index()
                        d.loc[:, 'source_id'] = entry_id

                        sources_by_year.append(d)


    sources = pd.DataFrame(sources)
    sources = sources.sort_values(by=['source_id'])

    if sources['source_id'].value_counts().max()>1:
        raise AssertionError('Some source_id is ambiguous')

    sources_by_year = pd.concat(sources_by_year).set_index('source_id').reset_index()

    # p = os.path.join(outdir, 'sources.parquet')
    p = 'openalex/{}/sources_main.parquet'.format(
        data_version
        )
    inout.export_plain_table(sources,p)

    # p = os.path.join(outdir, 'sources_by_year.parquet')
    p = 'openalex/{}/sources_by_year.parquet'.format(
        data_version
        )
    inout.export_plain_table(sources_by_year,p)                    




   

def works():

    location_from_primary_location = 0
    location_from_host_venue = 0         # these should become deprecated March 6th, 2023 https://docs.openalex.org/api-entities/works/work-object#host_venue-deprecated

    processed_entries = 0
    skipped_entries = 0


    export_classes = ['pubmed_id', 'pmc_id', 'neither']



    entity = 'works'

    data_version = inout.get_data_version('openalex')
    basedir = inout.get_input_path(
        'manual/openalex/{}/data/{}'.format(
            data_version, entity
        ), big=True)



    letter = entity[0].upper()

    forbidden_ids = _get_merged_ids(entity)



    folders = [f.path for f in os.scandir(basedir) if f.is_dir()]
    folders_in_order_to_process = sorted(folders)[::-1]    # https://docs.openalex.org/download-all-data/snapshot-data-format

    for subfolder in folders_in_order_to_process:    

        files = [f for f in os.listdir(subfolder) if os.path.isfile(os.path.join(subfolder, f))]
        files = [os.path.join(subfolder, x) for x in files if x.endswith('.gz')]

        for file in files:

            print(file)

            works, authors, collected_citing, collected_referenced, concepts = _initiate_collectors()

            shortened_file_path = os.sep.join(file.split(os.sep)[-2:])

            with gzip.open(file, 'rt', encoding='UTF-8') as zipfile:
                for line in zipfile:
                    entry = json.loads(line)

                    entry_id = _safely_establish_id(entry['id'], letter)


                    if entry_id in forbidden_ids:
                        continue
                    elif entry_id is not None:
                        forbidden_ids.add(entry_id)

                    
                    got_from_primary_location = False
                    if 'primary_location' in entry.keys():    # overly safe as on updated_date=2022-12-22 and before records do not have proper format
                        if entry['primary_location']:
                            if 'source' in entry['primary_location'].keys():
                                if entry['primary_location']['source']:
                                    if 'id' in entry['primary_location']['source'].keys():
                                        location_id = entry['primary_location']['source']['id']
                                        location_from_primary_location += 1
                                        got_from_primary_location = True
                            
                    if got_from_primary_location == False:    # will deprecate on 2023-03-06
                        location_id = entry['host_venue']['id'] # will deprecate on 2023-03-06
                        location_from_host_venue +=1
                    
                    if location_id is None:
                        location_id = None
                    else:
                        location_id = _safely_establish_id(location_id, 'S')

                    publication_type = entry['type']


                    work_record = {
                        'work_id': entry_id,
                        'source_id': location_id,
                        'doi': entry['doi'],
                        'year': entry['publication_year'],
                        'title': entry['title'],
                        'type': publication_type,
                        'is_retracted': entry['is_retracted']
                    }

                    export_class = _determine_export_class(entry)
                    if export_class == 'pubmed_id':
                        work_record['pubmed_id'] = int(entry['ids']['pmid'].replace(
                            'https://pubmed.ncbi.nlm.nih.gov/', ''))
                    elif export_class == 'pmc_id':
                        work_record['pmc_id'] = entry['ids']['pmid'].replace(
                            'https://pubmed.ncbi.nlm.nih.gov/', '')

                    works[export_class].append(work_record)

                    for author_number, author in enumerate(entry['authorships'], start=1):

                        if author['author']:
                            if author['author']['id']:
                                author_id = _safely_establish_id(author['author']['id'], 'A')
                            else:
                                author_id = None
                        else:
                            author_id = None

                        if 'is_corresponding' in author.keys():
                            corresponding = author['is_corresponding']
                        else:
                            corresponding = None

                        author_record = {
                            'work_id': entry_id,
                            'author_id': author_id,
                            'author_position': author['author_position'],
                            'author_number': author_number,
                            'is_corresponding': corresponding
                        }

                        authors[export_class].append(author_record)


                    for concept in entry['concepts']:
                        if 'id' in concept.keys():
                            concept_id = _safely_establish_id(concept['id'], 'C')
                        else:
                            concept_id = None

                        concept_record = {
                            'work_id': entry_id,
                            'concept_id': concept_id,
                            'score': concept['score']
                        }
                        concepts[export_class].append(concept_record)


                    referenced = [_safely_establish_id(x, letter) for x in entry['referenced_works']]

                    n = len(referenced)
                    if n > 0:
                        citing = entry_id    # [entry_id] * n
                        collected_citing[export_class].append(citing)
                        collected_referenced[export_class].append(referenced)


            shortened_file_path = os.sep.join(file.split(os.sep)[-2:])
            for export_class in export_classes:
                print(export_class)
                d = works[export_class]
                if len(d)>0:
                    d = pd.DataFrame(d)
                    p = 'openalex/{}/works_main/has_{}/{}'.format(
                        data_version,
                        export_class,
                        shortened_file_path.replace('.gz', '.parquet')
                        )
                    inout.export_plain_table(
                        d,
                        p
                    )
                    
                d = authors[export_class]
                if len(d)>0:
                    d = pd.DataFrame(d)
                    p = 'openalex/{}/works_authors/has_{}/{}'.format(
                        data_version,
                        export_class,
                        shortened_file_path.replace('.gz', '.parquet')
                        )
                    inout.export_plain_table(
                        d,
                        p
                    )
                    
                d = concepts[export_class]
                if len(d)>0:
                    d = pd.DataFrame(d)
                    p = 'openalex/{}/works_concepts/has_{}/{}'.format(
                        data_version,
                        export_class,
                        shortened_file_path.replace('.gz', '.parquet')
                        )

                    inout.export_plain_table(
                        d,
                        p
                    )                
                    
                citing = collected_citing[export_class]
                referenced = collected_referenced[export_class]
                
                if len(citing)>0:
                    if len(citing) != len(referenced):
                        raise AssertionError('Citing and referenced do not match.')
                    

                    d = pd.DataFrame(
                        {
                            'citing': citing,
                            'referenced': referenced
                        })
                    d = d.explode('referenced')
                    

                    # if export_class=='neither':
                    #     if file=='/Volumes/active_gustav_and_supplements/ACTIVE_gustav_big_data/input/manual/openalex/2023-02-27b/data/works/updated_date=2023-02-21/part_001.gz':
                    #         return d
  
                    p = 'openalex/{}/works_citations/has_{}/{}'.format(
                        data_version,
                        export_class,
                        shortened_file_path.replace('.gz', '.parquet')
                        )


                    inout.export_plain_table(
                        d,
                        p
                    )
            


def _get_merged_ids(entity):
    letter = entity[0].upper()

    # main_folder = openalex_folder

    data_version = inout.get_data_version('openalex')
    main_folder = inout.get_input_path(
        'manual/openalex/{}/data/'.format(
            data_version
        ), big=True)


    p = os.path.join(main_folder, f'merged_ids/{entity}')

    files = [f for f in os.listdir(p) if os.path.isfile(os.path.join(p, f))]
    files = [os.path.join(p, x) for x in files if x.endswith('.gz')]

    agg = []
    for file in files:
        agg.append(pd.read_csv(file))
    df = pd.concat(agg)

    if any(df['id'].str.contains('{}0'.format(letter))):
        raise AssertionError(
            'Encoding of IDs changed and no longer preserves assumptions of Gustav.')
    else:
        merged_ids = set(df['id'].str.replace(rf'^{letter}', '').astype(int))

    return merged_ids


def _safely_establish_id(openalex_id, letter):
    
    if openalex_id.startswith('https://openalex.org/'):
        openalex_id = openalex_id[21:]
    else:
        raise AssertionError('Encoding of identifiers changed')

    return openalex_id    


def _initiate_collectors():

    export_classes = ['pubmed_id', 'pmc_id', 'neither']


    authors = dict()
    works = dict()
    collected_citing = dict()
    collected_referenced = dict()
    concepts = dict()
    for export_class in export_classes:
        authors[export_class] = []
        works[export_class] = []
        collected_citing[export_class] = []
        collected_referenced[export_class] = []
        concepts[export_class] = []
    return works, authors, collected_citing, collected_referenced, concepts


def _determine_export_class(entry):
    if 'pmid' in entry['ids'].keys():
        pmid = entry['ids']['pmid']
        if pmid.startswith('https://pubmed.ncbi.nlm.nih.gov/PMC'):
            export_class = 'pmc_id'
        else:
            export_class = 'pubmed_id'
    else:
        export_class = 'neither'
    return export_class


