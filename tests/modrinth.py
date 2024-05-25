from fastapi.testclient import TestClient

from app import APP

client = TestClient(APP)

def test_main():
    response = client.get("/modrinth/")
    assert response.status_code == 200

def test_modrinth_project():
    response = client.get("/modrinth/projects/sodium")
    assert response.status_code == 200

def test_modrinth_projects():
    response = client.post("/modrinth/projects", json={"projectSlugs": ["sodium", "jei"]})
    assert response.status_code == 200

def test_modrinth_project_versions():
    response = client.get("/modrinth/projects/sodium/versions")
    assert response.status_code == 200

def test_modrinth_version():
    response = client.get("/modrinth/version/yaoBL9D9")
    assert response.status_code == 200

def test_modrinth_multi_versions():
    response = client.post("/modrinth/versions", json={"versionIds": ["yaoBL9D9", "Fz37KqRh"]})
    assert response.status_code == 200

def test_modrinth_hash():
    response = client.get("/modrinth/version_file/f3349dbd065cf75718fd0186d196e7e635e658e0?algorithm=sha1")
    assert response.status_code == 200

def test_modrinth_multi_hashes():
    response = client.post("/modrinth/version_files", json={"hashes": ["f3349dbd065cf75718fd0186d196e7e635e658e0", "1af975fd055377f419baccd1784a3b2ae252de66"], "algorithm": "sha1"})
    assert response.status_code == 200

def test_modrinth_tags():
    response = client.get("/modrinth/tag/category")
    assert response.status_code == 200
    response = client.get("/modrinth/tag/loader")
    assert response.status_code == 200
    response = client.get("/modrinth/tag/game_version")
    assert response.status_code == 200
    response = client.get("/modrinth/tag/donation_platform")
    assert response.status_code == 200
    response = client.get("/modrinth/tag/project_type")
    assert response.status_code == 200
    response = client.get("/modrinth/tag/side_type")
    assert response.status_code == 200

