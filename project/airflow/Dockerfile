FROM rocker/r-ver:4.4
# Dockerfile for R 4.4 with tidyverse and Python 3.10 with pandas
# Start with the rocker/r-ver:4.4 base image (based on ubuntu 24.04 LTS)

LABEL maintainer="Thomas Strehl <at062084@pm.me>"
LABEL description="R 4.4 and python 3.12 for data processing with Airflow LocalExecutor"

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PY_VER="3.12"
ARG PRJ_DIR="project/airflow"
ARG INV_AIRFLOW="inventory/config/airflow"

# locate ourselves somewhere
WORKDIR /export

# ==================================================================
# Install system dependencies (including PostgreSQL client)
# ==================================================================

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libcurl4-openssl-dev \
        libssl-dev \
        libxml2-dev \
        libcairo2-dev \
        libsqlite3-dev \
        libmariadbd-dev \
        libgit2-dev \
        libpq-dev \
        libssh2-1-dev \
        unixodbc-dev \
        build-essential \
        software-properties-common \
        net-tools \
        curl \
        python3.12-venv \
        postgresql-client \
        libharfbuzz-dev \
        libfribidi-dev \
        libfreetype6-dev \
        libpng-dev \
        libtiff5-dev \
        libjpeg-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


# ==================================================================
# Install pandas libs in venv /opt/venv/python-$PY_VER
# ==================================================================    

# Create venv for airflow and data processing
RUN mkdir -p /opt/venv/python-$PY_VER && \
    python$PY_VER -m venv /opt/venv/python-$PY_VER

# Upgrade pip in the Python virtual environment
RUN . /opt/venv/python-$PY_VER/bin/activate && \
    pip install --upgrade pip

# Set environment variable for venv
ENV PATH="/opt/venv/python-$PY_VER/bin:$PATH"
RUN PATH=$ENV_PATH && export $PATH

# Install packages for Streamlit, Airflow and EDA (including PostgreSQL driver)
COPY $PRJ_DIR/requirements.txt $PRJ_DIR/requirements.txt
RUN . /opt/venv/python-$PY_VER/bin/activate && \
    pip3 install psycopg2-binary && \
    pip3 install -r /export/project/airflow/requirements.txt && \
    pip list


# ==================================================================
# Install tidyverse package for R
# ==================================================================
RUN install2.r --error --skipinstalled --repos https://cran.wu.ac.at \
    nanoparquet \
    logger \
    igraph
RUN install2.r --error --skipinstalled --repos https://cran.wu.ac.at \
    tidyverse \
    tidyr \
    stringr
RUN rm -rf /tmp/downloaded_packages/


# ==================================================================
# Note: Scripts and DAGs are mounted from host via docker-compose volumes
# No need to copy them into the image - they're deployed separately by CI
# ==================================================================

# Run Airflow as root inside container with LocalExecutor
COPY $INV_AIRFLOW      $PRJ_DIR/config
RUN mkdir /root/airflow
RUN cp /export/project/airflow/config/airflow.cfg         /root/airflow || true
RUN cp /export/project/airflow/config/webserver_config.py /root/airflow || true


EXPOSE 8080

# Bootstrap path to inventory for shell, R and python
ENV INVENTORY_ROOT_DIR=/export/inventory
ENV PYTHONPATH=/export
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["/bin/bash"]
CMD ["/export/project/airflow/scripts/airflow_localexecutor.sh"]
