FROM python:3.10-slim-bookworm

LABEL maintainer="Thomas Strehl <at062084@pm.me>"
LABEL description="EDA with python 3.10 in Streamlit"

ENV PY_VER="3.10"
ARG PRJ_DIR="project/streamlit"
ARG INV_STREAMLIT="/inventory/config/streamlit"

# Locate ourselves somewhere
WORKDIR /export

# ==================================================================
# Install system dependencies required for Python and R packages
# ==================================================================

RUN apt-get update \
    && apt-get install -y \
        build-essential \
        software-properties-common \
        net-tools \
        curl \
        git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


# ==================================================================
# Create virtual env with python-$PY_VER for EDA libs (required by e.g. dataprep)
# ==================================================================

RUN mkdir venv && \
    python3 -m venv venv/python-$PY_VER && \
    . venv/python-$PY_VER/bin/activate && \
    pip3 install --upgrade pip

# EDA libs
COPY $PRJ_DIR/requirements_streamlit.txt $PRJ_DIR/requirements_streamlit.txt
RUN . venv/python-$PY_VER/bin/activate && \
    pip3 install -r /export/project/streamlit/requirements_streamlit.txt  && \
    pip list

# dtale libs: Installing together with other packages does not work out
COPY $PRJ_DIR/requirements_dtale.txt $PRJ_DIR/requirements_dtale.txt
RUN . venv/python-$PY_VER/bin/activate && \
    pip3 install -r /export/project/streamlit/requirements_dtale.txt && \
    pip list


# ==================================================================
# Copy application to folder /export in container
# ==================================================================
COPY $PRJ_DIR/scripts $PRJ_DIR/scripts
COPY $PRJ_DIR/doc $PRJ_DIR/doc
COPY $PRJ_DIR/images $PRJ_DIR/images
COPY $PRJ_DIR/notebooks $PRJ_DIR/notebooks

# Put config.toml in streamlit owner home
COPY $INV_STREAMLIT   $PRJ_DIR/config
RUN mkdir /root/.streamlit
RUN cp /export/project/streamlit/config/config.toml /root/.streamlit

# Bootstrap path to inventory for shell, R and python
ENV INVENTORY_ROOT_DIR=/export/inventory
ENV PYTHONPATH=/export

EXPOSE 8501
ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["venv/python-3.10/bin/streamlit", "run", "/export/project/streamlit/scripts/ode-streamlit.py", "--server.port=8501", "--server.address=0.0.0.0"]
