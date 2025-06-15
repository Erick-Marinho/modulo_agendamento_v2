from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Configurações da aplicação
    """

    # ==== Configurações do Postgres ====

    POSTGRES_USER: str = Field(..., description="Usuário do Postgres")
    POSTGRES_PASSWORD: str = Field(..., description="Senha do Postgres")
    POSTGRES_DB: str = Field(..., description="Nome do banco de dados")

    # ==== Configurações do Pgadmin ====

    PGADMIN_DEFAULT_EMAIL: str = Field(..., description="Email do Pgadmin")
    PGADMIN_DEFAULT_PASSWORD: str = Field(..., description="Senha do Pgadmin")


def mask_sensitive_data(value: str, show_chars: int = 4) -> str:
    """
    Máscara para dados sensíveis
    """
    if not value or len(value) <= show_chars:
        return "*" * len(value) if value else "Não definida"
    return "*" * (len(value) - show_chars) + value[-show_chars:]


settings = Settings()

if __name__ == "__main__":
    print("Configurações da aplicação:")
    print(f"POSTGRES_USER: {mask_sensitive_data(settings.POSTGRES_USER)}")
    print(f"POSTGRES_PASSWORD: {mask_sensitive_data(settings.POSTGRES_PASSWORD)}")
    print(f"POSTGRES_DB: {settings.POSTGRES_DB}")
    print(f"PGADMIN_DEFAULT_EMAIL: {settings.PGADMIN_DEFAULT_EMAIL}")
    print(
        f"PGADMIN_DEFAULT_PASSWORD: {mask_sensitive_data(settings.PGADMIN_DEFAULT_PASSWORD)}"
    )
