FROM python:latest

RUN apt update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    cmake-curses-gui \
    mesa-common-dev \
    mesa-utils \
    freeglut3-dev \
    ninja-build 

RUN mkdir -p vtk && \
    git clone --recursive https://gitlab.kitware.com/vtk/vtk.git vtk/source

RUN mkdir -p vtk/build && \
    cd vtk/build && \
    cmake -D VTK_WRAP_PYTHON=ON ../source \
    && make install && rm -rf /vtk

RUN git clone https://github.com/vcasellesb/stl2nii && \
    cd stl2nii && \
    git switch docker && \
    pip install -e .

ENTRYPOINT ["bash", "-c", "stl2nii -i /stl/*.stl -ref /ref/*.nii.gz"]