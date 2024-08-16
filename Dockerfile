FROM python:latest

RUN git clone https://github.com/vcasellesb/stl2nii && \
    cd stl2nii && \
    pip install -e .

ENTRYPOINT ["bash", "-c", "stl2nii -i /stl/*.stl -ref /ref/*.nii.gz"]