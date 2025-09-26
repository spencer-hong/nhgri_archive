# Tiramisu [![Python 3.9](https://img.shields.io/badge/python-3.9-blue.svg)](https://www.python.org/downloads/release/python-390/)

## Introduction

Docker-based platform to handle content relationships for an end-to-end archival artifacts pipeline. Intended to be used on standalone computing units to serve, access, and preserve documents, files, and their derivative artifacts. Tiramisu allows for distributed task management, frontend accessibility, metadata viewing, and graph-based database management. Most importantly, Tiramisu integrates a task manager with a graph database tailored for archival documents and processing using all open-source tools. We highly encourage you to adapt Tiramisu for your purposes; the as-is version is the barebones.

Please email BPSD consortium for the next generation platform which builds on Tiramisu and improves usability and diversity of computational models.

## Get started

You are most likely accessing this service in association to our manuscript **A digital archive reveals how a funding agency cooperated with academics to support a nascent field of science.** We encourage you to go through the `start_here.ipynb` associated with that manuscript repository which demonstrates all the key features of Tiramisu.

First, let Tiramisu know where the root location of your archive is by changing the field `TIRAMISU_ROOT` in `core/.env` file. Everything under this root directory will be tracked by Tiramisu (except for those under a blacklist and hidden files). This is where your documents are currently stored. The original documents will not be modified but their outputs will be tracked through Tiramisu. Then, set the field `NEO4J_PASSWORD` to be the password of your choice.

If you are on a AArch64 architecture, please move [`digest-0.1.0-cp39-cp39-manylinux_2_17_aarch64.manylinux2014_aarch64.whl`](tiramisu/core/rust/target/options/digest-0.1.0-cp39-cp39-manylinux_2_17_aarch64.manylinux2014_aarch64.whl) inside [`core/rust/target/options`](tiramisu/core/rust/target/options) to [`core/rust/target/wheels`](tiramisu/core/rust/target/wheels). Check that only one wheel file exists there. 

Then build and start Tiramisu inside `tiramisu` folder with  

```bash
docker-compose -f core/docker-compose_aarch64.yaml up --build
```

If you are on a x86_64 architecture, please move [`digest-0.1.0-cp39-cp39-manylinux_2_17_x86_64.manylinux2014_x86_64.whl`](tiramisu/core/rust/target/options/digest-0.1.0-cp39-cp39-manylinux_2_17_x86_64.manylinux2014_x86_64.whl) to [`core/rust/target/wheels`](tiramisu/core/rust/target/wheels). Check that only one wheel file exists there. 

Then build and start Tiramisu inside `tiramisu` folder with  

```bash
docker-compose -f core/docker-compose_x86_64.yaml up --build
```

Tiramisu will require ports 8080, 5005, 7474, 7687, 5000, 6379, 8085, 9998.

This will take few minutes for all Docker images to build. After building the images, it will serve all of the containers. You can add `--detach` flag to avoid occupying the terminal.

After the first build, subsequent starts can remove `--build`; otherwise, it will rebuild the service every single time.


**This version of Tiramisu is developed on x86_64 platforms and specifically tested on a Ubuntu 22.04.5 LTS system with 16 CPU cores**. 

> **Note**: Linux-based systems will require **rootless** Docker mode. MacOS Docker _essentially_ runs as rootless by default.

## Interacting with Tiramisu

- You can access possible Tiramisu actions by going to our website which will be hosted at http://localhost:8080
- The graph database is hosted at http://localhost:7474
- The task manager dashboard is hosted at http://localhost:8080/flower/dashboard
- The labeling interface is hosted at http://localhost:8085
- Flask API is hosted at http://localhost:8080/api
- Apache Tika is hosted at http://localhost:9998

## Limitations

Tiramisu is _not_ a pipeline. It does not contain any models to handle key document intelligence tasks such as page stream segmentation or document categorization. Versions of documents can be accessed via Tiramisu, modified **outside** of Tiramisu, then tracked back in Tiramisu. This was developed in part to avoid Docker builds that contain gigabytes of models and parameters.

Tiramisu, due to serving local files to a labeling interface, has a http file server provided by a reverse proxy service. This means that anyone access to http://localhost:8080/file/ can access any file. If you wish to remove this service (which means you will not be able to use the labeling interface), then comment out in [nginx.conf](core/nginx/conf.d/nginx.conf):

    # proxy to serving root directory for files
    location /file {
        root /;
        autoindex on;
    }

Tiramisu is not production-level. This Tiramisu version assumes that only authenticated users can access its local resources. Several aspects require modification before deploying in production.

## Uninstallation

To shut down the service,

    docker-compose -f core/docker-compose.yaml down


If you wish to remove Tiramisu at any point, you can simply erase `.tiramisu` in the path you set in `core/.env`. `.tiramisu` is a privileged folder that is created once Tiramisu runs inside the specified root directory to avoid Tiramisu changing your original archival files.

## FAQs
1. **My platform is not x86_64.**   
    The provided wheel file at `core/rust/target/wheels` will not work for your platform. You must create a wheel using the source code. To create a Python package using Rust code, you need to install Maturin to allow Rust binaries to be Python installable.

        pip install maturin

    To ensure that your binary can be executable in many OS environments, we will use the `manylinux` Docker container to create our Python wheel. Run

        docker run --rm -v $(pwd):/io ghcr.io/pyo3/maturin build --release -i python3.9
    
    in `core/rust`. Then remove the non-applicable wheel file and re-build the Docker system.

2. **I want to back up the graph database.**

    To save a snapshot of the database, you must enter the running Docker container called neo4j. You can use `docker ps` to find the neo4j container name. The following command will enter a container named `neo4j` and list existing databases.

        docker exec -it neo4j cypher-shell -u neo4j -p [password] -d system "SHOW DATABASES;"

    Find the database you wish to backup and stop the database.

        docker exec -it neo4j cypher-shell -u neo4j -p [password] -d system "STOP DATABASE [name of database];"
    
    Then, run the backup command.

        docker exec -it neo4j neo4j-admin dump --database=[name of database] --to=/backups/[name of backup].dump
    

    If you configured your Docker volumes correctly, [name of backup].dump should be placed in [root path]/.tiramisu/neo4j/backups/.

    Remember to start back up the database to respond to new queries.

        docker exec -it neo4j cypher-shell -u neo4j -p [password] -d system "START DATABASE [name of database];"

    To replace an existing databse with a backup dump you have created,

        docker exec -it neo4j neo4j-admin load --from=/backups/[name of dump].dump --database=[name of database] --force

    The database must be stopped before loading.

3. **I want to undo my actions.**

    You cannot undo steps in Tiramisu. However, every action is Tiramisu is reproducible. You will arrive at the same step if you remove Tiramisu and start the actions from the beginning.

4. **I want to add more Celery workers.**

    You can change `deploy: replicas: 1` in `core/docker-compose.yaml` for celery workers.
5. **I get a "permissions" error in Docker.**

    Most permissions error in Docker for Tiramisu will be due to the rootlessness of Tiramisu. This is intentional by design. You can either provide permissions separately by `chmod` or `chown` on the folders that are connected through Docker volume, or provide UID and GID directly to the containers in `core/docker-compose.yaml`.  

    You may also run this in default (rootful) docker, but we caution security risks associated with such action.
    
    If your LabelStudio is having this issue, you can create `.tiramisu/label-studio/media` and `.tiramisu/label-studio/export` folders and the re-run the Docker service. 

6. **I want to submit a task that is not in the Tiramisu Actions front page.**  
    You can submit either tasks to be run concurrently at http://localhost:8080/api/action/concurrent or sequentially in chain at http://localhost:8080/api/action/chain. 

7. **I'm getting a `no module found` error in frontend service.**

    Make sure to delete all docker volumes by doing `docker-compose down -v`. 


# Authors

Spencer Hong (spencerhong@u.northwestern.edu)  
Helio Tejedor 
