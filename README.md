# Team Crescendo 3rd Anniversary Bot

팀 크레센도는 3주년(2021. 1. 6.)을 맞이하여 [스티커를 모아라!](https://cafe.naver.com/teamcrescendocafe/1863) 이벤트를 진행했습니다.
이 이벤트를 원활히 운영하기 위한 디스코드 챗봇을 개발했습니다.

## Archived

이 프로젝트는 팀 크레센도 내부에서 사용하기 위한 목적으로만 개발되었습니다.
따라서 외부인은 이 프로젝트에서 개발한 모든 기능을 이용할 수는 없습니다.

디스코드 챗봇을 개발하는 과정에 참고가 되고자 소스 코드를 공개했습니다.
단, 3주년 이벤트는 이미 종료된 프로젝트기 때문에 추가적인 유지보수는 진행하지 않습니다.

## Getting Started

### Prerequisite

#### Database Management System

사용자의 스티커를 관리하기 위한 DBMS로 Postgres를 사용합니다.
자세한 내용은 [데이터베이스 연결 가이드](https://github.com/team-crescendo/3rd-anniversary-bot/blob/master/docs/CONNECT_DATABASE.md)를 참고해주세요.

#### Environment Variables

챗봇이 원활히 구동하기 위해서는 환경 변수를 통해 추가 정보를 제공해야합니다.
`.env.example` 양식을 참고하여 `.env` 파일을 적절히 작성해야합니다.

## Deployment

Docker를 이용해서 간편히 배포할 수 있습니다.
아래 스크립트는 [데이터베이스 연결 가이드](https://github.com/team-crescendo/3rd-anniversary-bot/blob/master/docs/CONNECT_DATABASE.md)에 따라 이미 `postgres` 컨테이너가 가동 중이라고 가정합니다.

```sh
docker network create 3rd-anniv
docker network connect 3rd-anniv postgres
docker build -t crsd-3rd-anniv:latest .
docker run --rm -d -v "$(pwd)/.env:/.env" --name 3rd-anniv-bot crsd-3rd-anniv:latest
docker network connect 3rd-anniv 3rd-anniv-bot
```

## Built with
* [team-crescendo/discord-py-boilerplate](https://github.com/team-crescendo/discord-py-boilerplate)
* [sqlalchemy](https://docs.sqlalchemy.org/en/13/)

## Authors
* [@GBS-Skile](https://github.com/GBS-Skile),
Technical Director of [Team Crescendo](https://github.com/team-crescendo)

### License
This project is licensed under the MIT License - see the
[LICENSE](https://github.com/team-crescendo/discord-py-boilerplate/blob/master/LICENSE)
for the details
