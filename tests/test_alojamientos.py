from datetime import UTC, datetime, timedelta

import jwt
import pytest

from conftest import crear_usuario_y_token

URL = "/api/v1/alojamientos"
DATOS = {"titulo": "Casa", "descripcion": "Casa tranquila", "precio_noche": 125.50, "ciudad": "Bogotá"}


def crear(client, headers):
    respuesta = client.post(URL, json=DATOS, headers=headers)
    assert respuesta.status_code == 201
    return respuesta.get_json()["data"]


def test_crud_publico_y_propietario(client, usuario_auth):
    respuesta = client.get(URL)
    assert respuesta.status_code == 200
    assert respuesta.get_json() == {"success": True, "data": []}
    alojamiento = crear(client, usuario_auth)
    assert set(alojamiento) == set(DATOS) | {"id", "usuario_id", "comodidades"}
    assert alojamiento["comodidades"] == []
    payload = jwt.decode(usuario_auth["Authorization"].split()[1], "test-key", algorithms=["HS256"])
    assert alojamiento["usuario_id"] == int(payload["sub"])
    from app.dominios.alojamientos.repositorios import AlojamientoRepositorio
    registro = AlojamientoRepositorio.obtener_por_id(alojamiento["id"])
    assert isinstance(registro.fecha_creacion, datetime)
    assert "fecha_creacion" not in alojamiento
    assert float(alojamiento["precio_noche"]) == 125.50
    url = f"{URL}/{alojamiento['id']}"
    respuesta = client.get(url)
    assert respuesta.status_code == 200
    assert respuesta.get_json()["data"] == alojamiento
    respuesta = client.get(URL)
    assert respuesta.status_code == 200
    assert respuesta.get_json()["data"] == [alojamiento]
    respuesta = client.patch(url, json={"titulo": "Casa nueva"}, headers=usuario_auth)
    assert respuesta.status_code == 200
    assert respuesta.get_json()["data"]["titulo"] == "Casa nueva"
    assert respuesta.get_json()["data"]["ciudad"] == DATOS["ciudad"]
    respuesta = client.delete(url, headers=usuario_auth)
    assert respuesta.status_code == 204
    assert respuesta.data == b""
    assert client.get(url).status_code == 404
    assert client.get(URL).get_json()["data"] == []


@pytest.mark.parametrize("metodo", ["post", "patch", "delete"])
@pytest.mark.parametrize("token", [None, "incorrecto", "expirado", "inexistente"])
def test_escritura_requiere_usuario_autenticado(client, metodo, token):
    headers = {}
    if token:
        if token in ("expirado", "inexistente"):
            token = jwt.encode({"sub": "99999", "exp": datetime.now(UTC) + timedelta(minutes=-1 if token == "expirado" else 5)}, "test-key", algorithm="HS256")
        headers["Authorization"] = f"Bearer {token}"
    respuesta = getattr(client, metodo)(URL if metodo == "post" else f"{URL}/999", json=DATOS, headers=headers)
    assert respuesta.status_code == 401
    assert respuesta.get_json()["success"] is False


@pytest.mark.parametrize("metodo", ["patch", "delete"])
def test_otro_usuario_no_puede_modificar(client, usuario_auth, metodo):
    alojamiento = crear(client, usuario_auth)
    _, otros_headers = crear_usuario_y_token(client, "otro")
    url = f"{URL}/{alojamiento['id']}"
    respuesta = getattr(client, metodo)(url, json={"titulo": "Intruso"}, headers=otros_headers)
    assert respuesta.status_code == 403
    assert client.get(url).get_json()["data"] == alojamiento


def test_admin_puede_modificar_y_eliminar(client, usuario_auth, admin_auth):
    alojamiento = crear(client, usuario_auth)
    url = f"{URL}/{alojamiento['id']}"
    assert client.patch(url, json={"ciudad": "Cali"}, headers=admin_auth).status_code == 200
    assert client.get(url).get_json()["data"]["ciudad"] == "Cali"
    assert client.delete(url, headers=admin_auth).status_code == 204


@pytest.mark.parametrize("metodo", ["get", "patch", "delete"])
def test_no_encontrado(client, usuario_auth, metodo):
    respuesta = getattr(client, metodo)(f"{URL}/999", json={"titulo": "Nueva"}, headers=usuario_auth)
    assert respuesta.status_code == 404
    assert respuesta.get_json()["success"] is False


@pytest.mark.parametrize("campo,valor", [
    ("titulo", ""), ("titulo", "   "), ("titulo", "x" * 201),
    ("descripcion", None), ("descripcion", " "), ("ciudad", ""), ("ciudad", "x" * 101),
    ("precio_noche", 0), ("precio_noche", -1), ("precio_noche", "NaN"),
    ("precio_noche", "Infinity"), ("precio_noche", True), ("precio_noche", "abc"),
    ("precio_noche", 1.234), ("precio_noche", 100000000),
    ("usuario_id", 999), ("id", 55), ("extra", "valor"),
])
@pytest.mark.parametrize("metodo", ["post", "patch"])
def test_validacion(client, usuario_auth, campo, valor, metodo):
    url = URL
    datos = {**DATOS, campo: valor}
    if metodo == "patch":
        alojamiento = crear(client, usuario_auth)
        url += f"/{alojamiento['id']}"
        datos = {campo: valor}
    respuesta = getattr(client, metodo)(url, json=datos, headers=usuario_auth)
    if campo == "precio_noche" and valor == 1.234:
        assert respuesta.status_code == (201 if metodo == "post" else 200)
        assert respuesta.get_json()["data"]["precio_noche"] == 1.23
        return
    if metodo == "patch" and valor is None:
        assert respuesta.status_code == 200
        assert respuesta.get_json()["data"] == alojamiento
        return
    assert respuesta.status_code == 400
    assert respuesta.get_json()["success"] is False
    if metodo == "patch":
        assert client.get(url).get_json()["data"] == alojamiento
    else:
        assert client.get(URL).get_json()["data"] == []


@pytest.mark.parametrize("campo", list(DATOS))
def test_campos_requeridos(client, usuario_auth, campo):
    datos = dict(DATOS)
    del datos[campo]
    assert client.post(URL, json=datos, headers=usuario_auth).status_code == 400


@pytest.mark.parametrize("cuerpo", ["{", "[]", "null", "{}"])
@pytest.mark.parametrize("metodo", ["post", "patch"])
def test_cuerpo_invalido(client, usuario_auth, cuerpo, metodo):
    url = URL
    if metodo == "patch":
        url += f"/{crear(client, usuario_auth)['id']}"
    respuesta = getattr(client, metodo)(url, data=cuerpo, content_type="application/json", headers=usuario_auth)
    assert respuesta.status_code == (200 if metodo == "patch" and cuerpo == "{}" else 400)


@pytest.mark.parametrize("campo", list(DATOS))
def test_patch_null_no_sobrescribe(client, usuario_auth, campo):
    alojamiento = crear(client, usuario_auth)
    url = f"{URL}/{alojamiento['id']}"
    respuesta = client.patch(url, json={campo: None}, headers=usuario_auth)
    assert respuesta.status_code == 200
    assert respuesta.get_json()["data"] == alojamiento
    assert client.get(url).get_json()["data"] == alojamiento


def test_limites_validos_y_patch_mixto(client, usuario_auth):
    respuesta = client.post(URL, json={**DATOS, "titulo": "x" * 200, "precio_noche": "0.01"}, headers=usuario_auth)
    assert respuesta.status_code == 201
    alojamiento = respuesta.get_json()["data"]
    assert alojamiento["precio_noche"] == 0.01
    respuesta = client.patch(f"{URL}/{alojamiento['id']}", json={"titulo": None, "ciudad": "Cali"}, headers=usuario_auth)
    assert respuesta.status_code == 200
    assert respuesta.get_json()["data"]["titulo"] == alojamiento["titulo"]
    assert respuesta.get_json()["data"]["ciudad"] == "Cali"


def test_precio_inferior_al_minimo(client, usuario_auth):
    assert client.post(URL, json={**DATOS, "precio_noche": "0.001"}, headers=usuario_auth).status_code == 400
