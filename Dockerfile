# builder는 배포 환경에서 사용할 패키지를 설치하는 역할을 수행합니다.
FROM python:3.8-slim AS builder
RUN apt-get update
RUN apt-get install -y --no-install-recommends build-essential gcc
COPY requirements.txt /tmp/requirements.txt
RUN pip install --user --no-warn-script-location -r /tmp/requirements.txt


FROM python:3.8-slim AS app
RUN apt-get update
RUN ln -sf /usr/share/zoneinfo/Asia/Seoul /etc/localtime && dpkg-reconfigure -f noninteractive tzdata

COPY --from=builder /root/.local /root/.local

COPY logging.json logging.json
COPY src /src/

ENV PATH=/root/.local/bin:$PATH
CMD ["python", "/src/bot.py"]
