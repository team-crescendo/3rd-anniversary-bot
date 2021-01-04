# 데이터베이스 연결 가이드

DBMS로는 PostgreSQL, DB 커넥터로는 psycopg2를 사용합니다.
환경변수 `PSYCOPG2_CONNECTION`에 `.env.example`에 맞춰 적절한 Connection String을 제공하면 연동됩니다.

## PostgreSQL이 설치되지 않은 경우

Docker를 이용하여 PostgreSQL을 간편히 구동할 수 있습니다.

```shell
docker pull postgres
docker volume create pgdata
docker run --name postgres -d -p 5433:5432 -v pgdata:/var/lib/postgresql/data -e POSTGRES_PASSWORD="PASSWORD" postgres
```

이 경우 환경변수는 `postgres:PASSWORD@localhost:5433/postgres`로 설정하면 됩니다.

## 스키마 마이그레이션

```shell
$ python
>>> from dotenv import load_dotenv
>>> load_dotenv()
>>> from src.models import Base, engine, user
>>> Base.metadata.create_all(engine)
```
