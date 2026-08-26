FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MPLBACKEND=Agg

RUN groupadd --gid 10001 sandbox \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin sandbox \
    && pip install --no-cache-dir \
       pandas numpy openpyxl python-docx pypdf matplotlib

WORKDIR /opt/sandbox
COPY backend/runtime/child_runner.py /opt/sandbox/child_runner.py
RUN chown -R sandbox:sandbox /opt/sandbox

USER 10001:10001
CMD ["sleep", "infinity"]
