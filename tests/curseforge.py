from fastapi.testclient import TestClient

from app import APP

client = TestClient(APP)

def test_main():
    response = client.get("/curseforge/")
    assert response.status_code == 200

def test_curseforge_mod():
    response = client.get("/curseforge/mods/238222")
    assert response.status_code == 200

def test_curseforge_mods():
    response = client.post("/curseforge/mods", json={"modIds": [238222, 348521]})
    assert response.status_code == 200

def test_curseforge_mod_files():
    response = client.get("/curseforge/mods/348521/files")
    assert response.status_code == 200

def test_curseforge_file():
    response = client.get("/curseforge/mods/348521/files/4973457")
    assert response.status_code == 200

def test_curseforge_files():
    response = client.post("/curseforge/mods/files", json={"fileIds": [4973457, 5248772]})
    assert response.status_code == 200

def test_curseforge_fingerprints():
    response = client.post("/curseforge/fingerprints", json={"fingerprints": [1552132089, 320753275]})
    assert response.status_code == 200