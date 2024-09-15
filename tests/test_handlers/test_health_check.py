import json

from starlette import status


class TestHealthCheckHandler:
    @staticmethod
    def get_url() -> str:
        return "/api/v1/health_check"

    async def test_ping_application(self, client):
        response = await client.get(url=self.get_url() + '/ping_application')
        assert response.status_code == status.HTTP_200_OK
        assert json.loads(response.content) == {
            "message": "Application worked!"
        }

    async def test_ping_database(self, client):
        response = await client.get(url=self.get_url() + '/ping_database')
        assert response.status_code == status.HTTP_200_OK
        assert json.loads(response.content) == {
            "message": "Database worked!"
        }
