# Mini Social Media App

Aplikacja webowa typu mini social media zbudowana w architekturze mikrousług, wdrożona na Google Cloud Run z automatycznym pipeline CI/CD.

## Jak działa

Użytkownik może zarejestrować się, zalogować, a następnie publikować, edytować i usuwać posty. Po zalogowaniu aplikacja otrzymuje token JWT, który dołączany jest do każdego żądania wymagającego autoryzacji.

## Architektura

```
┌─────────────┐     JWT token      ┌──────────────────┐
│   Frontend  │ ──────────────────▶│   post-service   │
│  (React +   │                    │   (FastAPI)       │
│   nginx)    │ ──────────────────▶│   auth-service   │
└─────────────┘  login/register    │   (FastAPI)       │
                                   └──────────────────┘
                                            │
                                     ┌──────────────┐
                                     │  PostgreSQL  │
                                     │  (Supabase)  │
                                     └──────────────┘
```

### Serwisy

| Serwis | Port | Opis |
|---|---|---|
| auth-service | 8000 | Rejestracja, logowanie, wystawianie tokenów JWT |
| post-service | 8001 | CRUD na postach, weryfikacja tokenów JWT |
| frontend | 80 | Interfejs użytkownika (React), serwowany przez nginx |

## Technologie

- **Backend:** Python, FastAPI, uvicorn
- **Frontend:** React, nginx
- **Baza danych:** PostgreSQL (psycopg2)
- **Autentykacja:** JWT (PyJWT), bcrypt
- **Konteneryzacja:** Docker, Docker Compose
- **CI/CD:** GitHub Actions
- **Chmura:** Google Cloud Run
- **Rejestr obrazów:** Docker Hub

## Bezpieczeństwo

- Hasła haszowane algorytmem **bcrypt** z losową solą — oryginalne hasło nigdy nie jest przechowywane
- Sesje oparte na tokenach **JWT** podpisanych algorytmem HS256, ważnych przez 1 godzinę
- Cała komunikacja przez **HTTPS** (certyfikat TLS zapewniany automatycznie przez Google Cloud Run)

## Operacje CRUD

| Operacja | Endpoint | Metoda |
|---|---|---|
| Utwórz post | `/posts` | POST |
| Pobierz posty | `/posts` | GET |
| Pobierz post | `/posts/{id}` | GET |
| Edytuj post | `/posts/{id}` | PUT |
| Usuń post | `/posts/{id}` | DELETE |

## Uruchomienie lokalne

```bash
docker compose up --build
```

Aplikacja dostępna pod adresem `http://localhost:8501`.

Wymagana zmienna środowiskowa `DATABASE_URL` z connection stringiem do PostgreSQL.

## CI/CD

Każdy push na gałąź `main` uruchamia automatyczny pipeline GitHub Actions:

1. Instalacja zależności Python
2. Testy jednostkowe (auth-service, post-service)
3. Testy end-to-end (integracja obu serwisów)
4. Budowanie obrazów Docker
5. Publikacja na Docker Hub

Pipeline zatrzymuje się jeśli jakikolwiek test nie przejdzie — wdrożenie następuje tylko po pozytywnym przejściu wszystkich testów.

## Testy

```bash
# Testy jednostkowe
pytest auth-service/tests/
pytest post-service/tests/

# Testy end-to-end
pytest tests_e2e/
```

## Wdrożenie (Google Cloud Run)

```bash
gcloud run deploy auth-service \
  --image docker.io/spluthietaco/auth-service:latest \
  --platform managed --region europe-west1 \
  --allow-unauthenticated --port 8000 \
  --set-env-vars "SECRET_KEY=...,DATABASE_URL=..."

gcloud run deploy post-service \
  --image docker.io/spluthietaco/post-service:latest \
  --platform managed --region europe-west1 \
  --allow-unauthenticated --port 8001 \
  --set-env-vars "SECRET_KEY=...,DATABASE_URL=..."

gcloud run deploy frontend \
  --image docker.io/spluthietaco/frontend:latest \
  --platform managed --region europe-west1 \
  --allow-unauthenticated --port 80
```
