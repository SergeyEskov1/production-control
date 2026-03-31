from fastapi import FastAPI

# Создаём экземпляр FastAPI приложения
# title отображается в автодокументации на /docs
app = FastAPI(title="Production Control API")

# Healthcheck — Docker проверяет этот эндпоинт каждые 30 секунд
# Если не отвечает — контейнер считается упавшим
@app.get("/health")
async def health():
    return {"status": "ok"}
