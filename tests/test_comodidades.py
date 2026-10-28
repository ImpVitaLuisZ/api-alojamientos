import pytest

from conftest import crear_usuario_y_token
from test_alojamientos import crear as crear_alojamiento

URL = "/api/v1/comodidades"


def crear_comodidad(client, admin_auth, nombre="Wifi"):
    respuesta = client.post(URL, json={"nombre": nombre}, headers=admin_auth)
    assert respuesta.status_code == 201
    return respuesta.get_json()["data"]


@pytest.fixture
def escenario(client, usuario_auth, admin_auth):
    alojamiento = crear_alojamiento(client, usuario_auth)
    comodidad = crear_comodidad(client, admin_auth)
    return f"/api/v1/alojamientos/{alojamiento['id']}", comodidad


def test_admin_crea_comodidad(client, admin_auth):
    comodidad = crear_comodidad(client, admin_auth)
    assert set(comodidad) == {"id", "nombre"}
    assert comodidad["id"] > 0
    assert comodidad["nombre"] == "Wifi"


def test_usuario_no_crea_comodidad(client, usuario_auth):
    respuesta = client.post(URL, json={"nombre": "Wifi"}, headers=usuario_auth)
    assert respuesta.status_code == 403
    assert respuesta.get_json()["success"] is False


def test_comodidad_duplicada(client, admin_auth):
    comodidad = crear_comodidad(client, admin_auth)
    respuesta = client.post(URL, json={"nombre": "Wifi"}, headers=admin_auth)
    assert respuesta.status_code == 409
    assert respuesta.get_json()["success"] is False
    assert client.get(URL).get_json()["data"] == [comodidad]


def test_listado_publico(client, admin_auth):
    respuesta = client.get(URL)
    assert respuesta.status_code == 200
    assert respuesta.get_json() == {"success": True, "data": []}
    comodidad = crear_comodidad(client, admin_auth)
    respuesta = client.get(URL)
    assert respuesta.status_code == 200
    assert respuesta.get_json() == {"success": True, "data": [comodidad]}


def test_propietario_asocia(client, usuario_auth, escenario):
    url, comodidad = escenario
    respuesta = client.patch(url + "/comodidades", json={"comodidades_ids": [comodidad["id"]]}, headers=usuario_auth)
    assert respuesta.status_code == 200
    assert respuesta.get_json()["success"] is True
    assert respuesta.get_json()["data"]["comodidades"] == [comodidad]
    assert client.get(url).get_json()["data"]["comodidades"] == [comodidad]
    assert client.get("/api/v1/alojamientos").get_json()["data"][0]["comodidades"] == [comodidad]


def test_otro_usuario_no_asocia(client, escenario):
    url, comodidad = escenario
    _, headers = crear_usuario_y_token(client, "otro")
    respuesta = client.patch(url + "/comodidades", json={"comodidades_ids": [comodidad["id"]]}, headers=headers)
    assert respuesta.status_code == 403
    assert client.get(url).get_json()["data"]["comodidades"] == []


def test_comodidad_inexistente(client, usuario_auth, escenario):
    url, comodidad = escenario
    assert client.patch(url + "/comodidades", json={"comodidades_ids": [comodidad["id"]]}, headers=usuario_auth).status_code == 200
    respuesta = client.patch(url + "/comodidades", json={"comodidades_ids": [comodidad["id"], 999999]}, headers=usuario_auth)
    assert respuesta.status_code == 400
    assert respuesta.get_json()["success"] is False
    assert client.get(url).get_json()["data"]["comodidades"] == [comodidad]


def test_admin_reemplaza_deduplica_y_vacia(client, admin_auth, escenario):
    url, primera = escenario
    segunda = crear_comodidad(client, admin_auth, "Piscina")
    for ids, esperado in [([primera["id"], segunda["id"], primera["id"]], [primera, segunda]), ([segunda["id"]], [segunda]), ([], [])]:
        respuesta = client.patch(url + "/comodidades", json={"comodidades_ids": ids}, headers=admin_auth)
        assert respuesta.status_code == 200
        assert respuesta.get_json()["data"]["comodidades"] == esperado
        assert client.get(url).get_json()["data"]["comodidades"] == esperado
    assert client.get(URL).get_json()["data"] == [primera, segunda]


@pytest.mark.parametrize("datos", [{}, {"comodidades_ids": None}, {"comodidades_ids": "1"}, {"comodidades_ids": [True]}, {"comodidades_ids": [1.5]}, {"comodidades_ids": ["1"]}, {"comodidades_ids": [0]}, {"comodidades_ids": [-1]}])
def test_ids_invalidos(client, usuario_auth, escenario, datos):
    url, _ = escenario
    respuesta = client.patch(url + "/comodidades", json=datos, headers=usuario_auth)
    assert respuesta.status_code == 400
    assert client.get(url).get_json()["data"]["comodidades"] == []


@pytest.mark.parametrize("nombre", [None, "", "   ", "x" * 101])
def test_nombre_invalido(client, admin_auth, nombre):
    assert client.post(URL, json={"nombre": nombre}, headers=admin_auth).status_code == 400


def test_escrituras_sin_token(client):
    assert client.post(URL, json={"nombre": "Wifi"}).status_code == 401
    assert client.patch("/api/v1/alojamientos/999/comodidades", json={"comodidades_ids": []}).status_code == 401


def test_alojamiento_inexistente(client, usuario_auth):
    respuesta = client.patch("/api/v1/alojamientos/999/comodidades", json={"comodidades_ids": []}, headers=usuario_auth)
    assert respuesta.status_code == 404
    assert respuesta.get_json()["success"] is False


def test_eliminar_alojamiento_con_comodidades(client, usuario_auth, escenario):
    url, comodidad = escenario
    assert client.patch(url + "/comodidades", json={"comodidades_ids": [comodidad["id"]]}, headers=usuario_auth).status_code == 200
    assert client.delete(url, headers=usuario_auth).status_code == 204
    assert client.get(URL).get_json()["data"] == [comodidad]
    from app import db
    from app.dominios.comodidades.modelos import alojamiento_comodidad
    assert db.session.execute(db.select(alojamiento_comodidad)).all() == []
