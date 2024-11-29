class TestAuthMiddleware:

    def test_public_route_access(self, client):
        response = client.get("/public")
        assert response.status_code == 200
        assert response.json() == {"message": "Public"}

    def test_private_route_access_no_token(self, client):
        response = client.get("/private", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/login"

    def test_private_route_access_valid_token(self, client, valid_token):
        client.cookies.set("token", valid_token)
        response = client.get("/private")
        assert response.status_code == 200
        assert response.json() == {"message": "Private"}

    def test_private_route_access_invalid_token(self, client, invalid_token):
        client.cookies.set("token", invalid_token)
        response = client.get("/private", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/login"

    def test_dynamic_route_access_no_token(self, client):
        response = client.get("/dynamic/123", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/login"

    def test_login_route_success(self, client):
        response = client.get("/login", follow_redirects=False)
        assert response.status_code == 200

    def test_dynamic_curly_bracket_route(self, client):
        response = client.get("/private-curly/id123456", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/login"
